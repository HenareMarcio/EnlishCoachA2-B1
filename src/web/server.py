"""Servidor FastAPI robusto para o English Speaking Coach com WebSocket e Gemini Live API.

Melhorias e Correções Arquiteturais:
1. Ciclo de vida moderno via lifespan (substituindo o depreciado on_event).
2. Tratamento correto de exceções assíncronas em asyncio.wait (sem engolir erros de tarefas em background).
3. Proteção contra envios e fechamentos duplicados em WebSocket (evita 'Cannot call send/close once closed').
4. Suporte a seleção de voz (SpeechConfig / PrebuiltVoiceConfig) via GEMINI_VOICE_NAME.
5. VAD e latência otimizados (sem dead-silence de 1.3s forçado).
6. Endpoint HTTP de diagnóstico (/api/health).
7. Gerenciamento seguro de sessão e mensagens no SQLite local.
"""

import asyncio
import base64
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketState
from google import genai
from google.genai import types

from src.config import (
    get_gemini_api_key,
    get_gemini_live_model,
    get_gemini_api_version,
    get_gemini_voice_name,
)
from src.storage import init_db, create_session, end_session, add_message
from src.agent.prompts import get_voice_system_prompt

# ---------------------------------------------------------------------------
# Logging Estruturado
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("coach_web_server")

# Diretórios
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


# ---------------------------------------------------------------------------
# Ciclo de Vida da Aplicação (FastAPI Lifespan)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa banco SQLite na subida e gerencia encerramento gracioso."""
    try:
        init_db()
        logger.info("Banco de dados SQLite inicializado com sucesso via lifespan.")
    except Exception as e:
        logger.error(f"Falha crítica ao inicializar o banco de dados: {e}")
    yield
    logger.info("Servidor web encerrado.")


app = FastAPI(
    title="English Speaking Coach - Live Audio Server",
    version="2.0",
    lifespan=lifespan,
)

# Monta arquivos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Endpoints HTTP
# ---------------------------------------------------------------------------
@app.get("/")
async def get_index() -> FileResponse:
    """Serve a interface web principal (index.html)."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(f"Arquivo {index_path} não encontrado.")
    return FileResponse(index_path)


@app.get("/api/health")
async def get_health() -> JSONResponse:
    """Endpoint de diagnóstico rápido para testar saúde do backend e configurações."""
    api_key_set = False
    try:
        key = get_gemini_api_key()
        api_key_set = bool(key and not key.startswith("sua_"))
    except Exception:
        pass

    return JSONResponse({
        "status": "ok",
        "live_model": get_gemini_live_model(),
        "api_version": get_gemini_api_version(),
        "voice": get_gemini_voice_name(),
        "api_key_configured": api_key_set,
        "static_dir_exists": STATIC_DIR.exists(),
    })


# ---------------------------------------------------------------------------
# Endpoint WebSocket para Live Audio Streaming
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_live_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket bidirecional para streaming de voz em tempo real."""
    await websocket.accept()
    logger.info("Cliente WebSocket conectado.")

    # Funções auxiliares para envio seguro (evita exceções de estado do WebSocket)
    async def safe_send_json(data: dict) -> bool:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_json(data)
                return True
            except Exception:
                return False
        return False

    async def safe_send_bytes(data: bytes) -> bool:
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_bytes(data)
                return True
            except Exception:
                return False
        return False

    # 1. Carrega credenciais e parâmetros
    try:
        api_key = get_gemini_api_key()
        live_model = get_gemini_live_model()
        api_version = get_gemini_api_version()
        voice_name = get_gemini_voice_name()
    except Exception as e:
        logger.error(f"Erro na configuração de inicialização: {e}")
        await safe_send_json({
            "type": "error",
            "message": f"Erro de configuração no servidor: {e}"
        })
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        return

    # 2. Inicializa sessão SQLite
    session_id: Optional[int] = None
    try:
        session_id = create_session(topic="Voice Conversation Live")
        logger.info(f"Sessão criada no SQLite com ID: {session_id}")
    except Exception as e:
        logger.error(f"Erro ao criar sessão no SQLite: {e}")
        await safe_send_json({
            "type": "error",
            "message": "Erro interno ao inicializar banco de dados da sessão."
        })
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()
        return

    # Notifica navegador sobre canal estabelecido
    await safe_send_json({
        "type": "connected",
        "session_id": session_id,
        "model": live_model,
        "api_version": api_version,
        "voice": voice_name,
    })

    # Acumuladores de transcrição para o turno atual
    turn_student_transcripts: List[str] = []
    turn_coach_transcripts: List[str] = []

    try:
        # 3. Inicializa cliente oficial google-genai
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version=api_version),
        )

        # 4. Configuração da Gemini Live API
        system_instruction = get_voice_system_prompt()

        # Configura voz e parâmetros de áudio
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name
                )
            )
        )

        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=system_instruction)]
            ),
            speech_config=speech_config,
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            http_options=types.HttpOptions(api_version=api_version),
        )

        logger.info(f"Conectando à Gemini Live API (Modelo: {live_model}, Voz: {voice_name}, Versão: {api_version})...")

        # 5. Abre sessão bidirecional assíncrona com o Gemini
        async with client.aio.live.connect(model=live_model, config=config) as live_session:
            logger.info("Sessão Gemini Live estabelecida com sucesso.")
            await safe_send_json({"type": "session_ready"})

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

                        # Frame binário: áudio PCM 16kHz do microfone
                        if "bytes" in msg and msg["bytes"]:
                            pcm_data = msg["bytes"]
                            browser_chunks += 1
                            browser_bytes += len(pcm_data)

                            if not first_browser_audio:
                                first_browser_audio = True
                                logger.info(f"Primeiro áudio do microfone recebido ({len(pcm_data)} bytes).")

                            if browser_chunks % 50 == 0:
                                logger.info(f"Áudio microfone: {browser_chunks} blocos ({browser_bytes} bytes acumulados).")

                            await live_session.send_realtime_input(
                                audio=types.Blob(
                                    data=pcm_data,
                                    mime_type="audio/pcm;rate=16000"
                                )
                            )
                        # Frame de texto/JSON: comandos de controle
                        elif "text" in msg and msg["text"]:
                            try:
                                data = json.loads(msg["text"])
                                if data.get("action") == "stop":
                                    logger.info("Comando de parada recebido do navegador.")
                                    break
                            except Exception:
                                pass
                except WebSocketDisconnect:
                    logger.info("Navegador encerrou o WebSocket (tarefa navegador).")
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    logger.warning(f"Exceção no envio de áudio do microfone: {ex}")
                    raise ex

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

                            # Interrupção detectada (o aluno começou a falar enquanto o coach falava)
                            if server_content.interrupted:
                                logger.info("Interrupção detectada (o aluno interrompeu o coach).")
                                turn_coach_transcripts.clear()
                                await safe_send_json({"type": "interrupted"})

                            # Transcrição parcial da fala do aluno (input_transcription)
                            if server_content.input_transcription and server_content.input_transcription.text:
                                text_chunk = server_content.input_transcription.text
                                turn_student_transcripts.append(text_chunk)
                                await safe_send_json({
                                    "type": "student_transcript",
                                    "text": text_chunk,
                                    "finished": bool(server_content.input_transcription.finished),
                                })

                            # Transcrição parcial da fala do coach (output_transcription)
                            if server_content.output_transcription and server_content.output_transcription.text:
                                text_chunk = server_content.output_transcription.text
                                turn_coach_transcripts.append(text_chunk)
                                await safe_send_json({
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
                                            logger.info(f"Primeiro áudio do Coach recebido ({len(audio_chunk)} bytes).")

                                        sent = await safe_send_bytes(audio_chunk)
                                        if not sent:
                                            logger.info("Cliente desconectado durante envio de áudio.")
                                            return

                            # Turno concluído: grava no SQLite e reinicia acumuladores
                            if server_content.turn_complete:
                                student_text = "".join(turn_student_transcripts).strip()
                                coach_text = "".join(turn_coach_transcripts).strip()

                                if student_text and session_id is not None:
                                    add_message(session_id, "student", student_text)
                                    logger.info(f"[Turno Aluno]: {student_text}")
                                if coach_text and session_id is not None:
                                    add_message(session_id, "coach", coach_text)
                                    logger.info(f"[Turno Coach]: {coach_text}")

                                turn_student_transcripts.clear()
                                turn_coach_transcripts.clear()
                                await safe_send_json({"type": "turn_complete"})

                except WebSocketDisconnect:
                    logger.info("Navegador desconectou durante leitura do Gemini.")
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    logger.warning(f"Exceção ao receber resposta da Live API: {ex}")
                    raise ex

            # Executa ambas as tarefas concorrentemente
            task_browser = asyncio.create_task(forward_browser_to_gemini())
            task_gemini = asyncio.create_task(forward_gemini_to_browser())

            done, pending = await asyncio.wait(
                [task_browser, task_gemini],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancela as tarefas pendentes graciosamente
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # CRÍTICO: Inspeciona tarefas finalizadas para não engolir exceções
            for task in done:
                exc = task.exception()
                if exc and not isinstance(exc, (asyncio.CancelledError, WebSocketDisconnect)):
                    raise exc

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Erro na sessão Live API: {err_msg}")

        # Tratamento explícito de cota / rate limit 429
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            friendly_err = (
                "Limite de requisições da API atingido (Cota 429 / RESOURCE_EXHAUSTED). "
                "Por favor, aguarde alguns instantes e tente novamente."
            )
        elif "400" in err_msg:
            friendly_err = f"Parâmetro inválido na solicitação da Live API: {err_msg}"
        else:
            friendly_err = f"Falha na conexão com o Gemini Live: {err_msg}"

        await safe_send_json({
            "type": "error",
            "message": friendly_err,
        })

    finally:
        # Salva transcrições pendentes caso a sessão termine no meio de um turno
        student_text = "".join(turn_student_transcripts).strip()
        coach_text = "".join(turn_coach_transcripts).strip()
        if session_id is not None:
            if student_text:
                try:
                    add_message(session_id, "student", student_text)
                except Exception as ex:
                    logger.warning(f"Erro ao salvar transcrição pendente do aluno: {ex}")
            if coach_text:
                try:
                    add_message(session_id, "coach", coach_text)
                except Exception as ex:
                    logger.warning(f"Erro ao salvar transcrição pendente do coach: {ex}")

            # Registra timestamp de encerramento da sessão
            try:
                end_session(session_id)
                logger.info(f"Sessão {session_id} finalizada com sucesso no SQLite.")
            except Exception as e:
                logger.warning(f"Erro ao finalizar sessão {session_id} no banco: {e}")

        # Notifica o cliente e fecha WebSocket de forma segura
        await safe_send_json({
            "type": "session_ended",
            "message": "Sessão de prática finalizada e salva com sucesso."
        })

        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn
    # Execução direta via: python src/web/server.py
    uvicorn.run("src.web.server:app", host="127.0.0.1", port=8000, reload=True)
