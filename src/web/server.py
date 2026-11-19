"""Servidor FastAPI para o English Speaking Coach com WebSocket e Gemini Live API."""

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

from src.config import (
    get_gemini_api_key,
    get_gemini_live_model,
    get_gemini_api_version,
)
from src.storage import init_db, create_session, end_session, add_message
from src.agent.prompts import get_voice_system_prompt

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("coach_web_server")

# Diretórios
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Inicialização do FastAPI
app = FastAPI(title="English Speaking Coach - Live Audio Server")

# Monta arquivos estáticos (se existirem)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    """Inicializa o banco de dados SQLite ao subir a aplicação."""
    init_db()
    logger.info("Banco de dados SQLite inicializado com sucesso.")


@app.get("/")
async def get_index() -> FileResponse:
    """Serve a interface web estática em arquivo único (index.html)."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(f"Arquivo {index_path} não encontrado.")
    return FileResponse(index_path)


@app.websocket("/ws")
async def websocket_live_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket para streaming de áudio bidirecional com a Gemini Live API.
    
    - Recebe áudio PCM 16-bit 16kHz do microfone do aluno via navegador.
    - Transmite para o modelo Gemini Live usando google-genai SDK.
    - Recebe áudio de resposta PCM 24kHz do Coach e envia em frames binários para o navegador.
    - Envia transcrições em tempo real do aluno e do coach como mensagens JSON.
    - Persiste as mensagens de cada turno no banco de dados SQLite local.
    """
    await websocket.accept()
    logger.info("Cliente WebSocket conectado.")

    # 1. Carrega credenciais e parâmetros com segurança no servidor
    try:
        api_key = get_gemini_api_key()
        live_model = get_gemini_live_model()
        api_version = get_gemini_api_version()
    except Exception as e:
        logger.error(f"Erro na configuração de inicialização: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Erro de configuração no servidor: {e}"
        })
        await websocket.close()
        return

    # 2. Cria uma nova sessão no banco de dados SQLite
    session_id: Optional[int] = None
    try:
        session_id = create_session(topic="Voice Conversation Live")
        logger.info(f"Sessão criada no SQLite com ID: {session_id}")
    except Exception as e:
        logger.error(f"Erro ao criar sessão no SQLite: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Erro interno ao inicializar banco de dados da sessão."
        })
        await websocket.close()
        return

    # Informa o navegador que o canal foi estabelecido
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
        "model": live_model,
        "api_version": api_version,
    })

    # Acumuladores de transcrição para o turno atual (para salvar no SQLite ao final do turno)
    turn_student_transcripts: List[str] = []
    turn_coach_transcripts: List[str] = []

    try:
        # 3. Inicializa o cliente oficial google-genai
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version=api_version),
        )

        # 4. Configura a sessão da Live API adaptada para voz
        system_instruction = get_voice_system_prompt()
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=system_instruction)]
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            http_options=types.HttpOptions(api_version=api_version),
        )

        logger.info(f"Conectando à Gemini Live API (Modelo: {live_model}, Versão: {api_version})...")

        # 5. Abre a sessão bidirecional assíncrona com o Gemini
        async with client.aio.live.connect(model=live_model, config=config) as live_session:
            logger.info("Sessão Gemini Live estabelecida com sucesso.")
            await websocket.send_json({"type": "session_ready"})

            # Tarefa A: Ler dados do navegador e enviar para o Gemini
            async def forward_browser_to_gemini():
                first_browser_audio = False
                browser_chunks = 0
                browser_bytes = 0
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            logger.info("Navegador desconectou (websocket.disconnect).")
                            break

                        # Se receber frame binário: áudio PCM 16kHz do microfone
                        if "bytes" in msg and msg["bytes"]:
                            pcm_data = msg["bytes"]
                            browser_chunks += 1
                            browser_bytes += len(pcm_data)

                            if not first_browser_audio:
                                first_browser_audio = True
                                logger.info(f"Primeiro bloco de áudio recebido do navegador ({len(pcm_data)} bytes).")

                            if browser_chunks % 50 == 0:
                                logger.info(f"Áudio do navegador: {browser_chunks} blocos recebidos ({browser_bytes} bytes acumulados).")

                            await live_session.send_realtime_input(
                                audio=types.Blob(
                                    data=pcm_data,
                                    mime_type="audio/pcm;rate=16000"
                                )
                            )
                        # Se receber frame de texto/JSON: comandos de controle
                        elif "text" in msg and msg["text"]:
                            try:
                                data = json.loads(msg["text"])
                                if data.get("action") == "stop":
                                    logger.info("Comando de parada recebido do navegador.")
                                    break
                            except Exception:
                                pass
                except WebSocketDisconnect:
                    logger.info("Navegador desconectou o WebSocket.")
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    logger.warning(f"Exceção ao encaminhar áudio do navegador: {ex}")

            # Tarefa B: Ler respostas do Gemini e enviar para o navegador
            async def forward_gemini_to_browser():
                nonlocal turn_student_transcripts, turn_coach_transcripts
                first_gemini_audio = False
                try:
                    while True:
                        async for response in live_session.receive():
                            server_content = response.server_content
                            if not server_content:
                                continue

                            # Se o aluno começar a falar enquanto o coach fala (interrupção)
                            if server_content.interrupted:
                                logger.info("Interrupção detectada (o aluno interrompeu o coach).")
                                await websocket.send_json({"type": "interrupted"})

                            # Transcrição parcial da fala do aluno (input_transcription)
                            if server_content.input_transcription and server_content.input_transcription.text:
                                text_chunk = server_content.input_transcription.text
                                turn_student_transcripts.append(text_chunk)
                                logger.info(f"[Transcrição Parcial Aluno]: {text_chunk}")
                                await websocket.send_json({
                                    "type": "student_transcript",
                                    "text": text_chunk,
                                    "finished": bool(server_content.input_transcription.finished),
                                })

                            # Transcrição parcial da fala do coach (output_transcription)
                            if server_content.output_transcription and server_content.output_transcription.text:
                                text_chunk = server_content.output_transcription.text
                                turn_coach_transcripts.append(text_chunk)
                                logger.info(f"[Transcrição Parcial Coach]: {text_chunk}")
                                await websocket.send_json({
                                    "type": "coach_transcript",
                                    "text": text_chunk,
                                    "finished": bool(server_content.output_transcription.finished),
                                })

                            # Áudio falado pelo coach (PCM 24kHz)
                            if server_content.model_turn and server_content.model_turn.parts:
                                for part in server_content.model_turn.parts:
                                    if part.inline_data and part.inline_data.data:
                                        audio_chunk = part.inline_data.data
                                        if isinstance(audio_chunk, str):
                                            audio_chunk = base64.b64decode(audio_chunk)

                                        if not first_gemini_audio:
                                            first_gemini_audio = True
                                            logger.info(f"Primeiro áudio recebido do Gemini ({len(audio_chunk)} bytes).")

                                        await websocket.send_bytes(audio_chunk)

                            # Turno concluído: grava transcrições no SQLite e reinicia acumuladores
                            if server_content.turn_complete:
                                student_text = "".join(turn_student_transcripts).strip()
                                coach_text = "".join(turn_coach_transcripts).strip()

                                if student_text:
                                    add_message(session_id, "student", student_text)
                                    logger.info(f"[Turno Concluído - Aluno]: {student_text}")
                                if coach_text:
                                    add_message(session_id, "coach", coach_text)
                                    logger.info(f"[Turno Concluído - Coach]: {coach_text}")

                                turn_student_transcripts.clear()
                                turn_coach_transcripts.clear()
                                await websocket.send_json({"type": "turn_complete"})

                except WebSocketDisconnect:
                    logger.info("Navegador desconectou durante leitura do Gemini.")
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    logger.warning(f"Exceção ao receber resposta do Gemini: {ex}")
                    raise ex

            # Executa ambas as tarefas concorrentemente até que uma termine
            task_browser = asyncio.create_task(forward_browser_to_gemini())
            task_gemini = asyncio.create_task(forward_gemini_to_browser())

            done, pending = await asyncio.wait(
                [task_browser, task_gemini],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancela as tarefas pendentes
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Erro na sessão Live API: {err_msg}")

        # Tratamento explícito de cota / rate limit 429
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            friendly_err = (
                "Limite de requisições da API atingido (Cota 429 / RESOURCE_EXHAUSTED). "
                "Por favor, aguarde alguns instantes e tente novamente."
            )
        else:
            friendly_err = f"Falha na conexão com o Gemini Live: {err_msg}"

        try:
            await websocket.send_json({
                "type": "error",
                "message": friendly_err,
            })
        except Exception:
            pass

    finally:
        # Salva qualquer transcrição residual não persistida
        student_text = "".join(turn_student_transcripts).strip()
        coach_text = "".join(turn_coach_transcripts).strip()
        if session_id is not None:
            if student_text:
                add_message(session_id, "student", student_text)
            if coach_text:
                add_message(session_id, "coach", coach_text)

            # Registra o timestamp de encerramento da sessão
            try:
                end_session(session_id)
                logger.info(f"Sessão {session_id} finalizada no SQLite.")
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão {session_id} no banco: {e}")

        # Notifica o cliente do fim da sessão
        try:
            await websocket.send_json({
                "type": "session_ended",
                "message": "Sessão de prática finalizada e salva com sucesso."
            })
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    # Permite rodar diretamente via: python src/web/server.py
    uvicorn.run("src.web.server:app", host="127.0.0.1", port=8000, reload=True)
