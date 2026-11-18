"""Implementação do CoachAgent e integração robusta com o Google Gemini."""

import json
import socket
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import sqlite3

from src.config import get_gemini_api_key, get_gemini_model
from src.storage.repository import add_error, add_message, get_last_error, get_top_errors
from .prompts import INITIAL_GREETING, VALID_CATEGORIES, build_system_prompt


# ---------------------------------------------------------------------------
# Estruturas de Dados Tipadas (Saída Estruturada)
# ---------------------------------------------------------------------------

@dataclass
class ErrorDetail:
    """Detalhes estruturados do erro principal corrigido no turno."""
    category: str
    original: str
    corrected: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class CoachResponse:
    """Resposta do tutor contendo a mensagem falada e o erro detectado."""
    reply: str
    error_detected: Optional[ErrorDetail] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reply": self.reply,
            "error_detected": self.error_detected.to_dict() if self.error_detected else None,
        }


# ---------------------------------------------------------------------------
# Hierarquia Oficial de Exceções da API
# ---------------------------------------------------------------------------

class APIError(Exception):
    """Erro base para respostas de erro da API Gemini."""
    def __init__(self, code: int, message: str, status: str = ""):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(f"{code} {status}: {message}")


class ClientError(APIError):
    """Erros de cliente HTTP 4xx (ex: 429 Rate Limit / Quota Exceeded, 400 Bad Request)."""
    pass


class ServerError(APIError):
    """Erros de servidor HTTP 5xx (ex: 500 Internal Error, 503 Model Unavailable/Overloaded)."""
    pass


# ---------------------------------------------------------------------------
# Classe Principal do Agente
# ---------------------------------------------------------------------------

class CoachAgent:
    """Tutor conversacional de inglês baseado na API Google Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        connection: Optional[sqlite3.Connection] = None,
    ):
        """Inicializa o agente sem nunca expor a chave de API em logs ou saídas."""
        self.api_key = api_key if api_key else get_gemini_api_key()
        self.model = model if model else get_gemini_model()
        self.connection = connection
        self.history: List[Dict[str, Any]] = []

    def get_greeting(self) -> str:
        """Retorna a saudação inicial para abertura do diálogo no CLI."""
        return INITIAL_GREETING

    def _call_gemini_endpoint(self, system_instruction: str, contents: List[Dict[str, Any]]) -> str:
        """Executa a requisição HTTP POST para a API do Gemini com timeout e tratamento de erros."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.7,
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data_bytes, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                response_text = res.read().decode("utf-8")
                return response_text

        except urllib.error.HTTPError as e:
            raw_err = e.read().decode("utf-8")
            err_msg = ""
            status_str = ""
            try:
                err_json = json.loads(raw_err).get("error", {})
                err_msg = err_json.get("message", raw_err)
                status_str = err_json.get("status", "")
            except Exception:
                err_msg = raw_err

            if e.code == 429:
                raise ClientError(
                    code=429,
                    message="Limite de requisições da API atingido (cota 429). Aguarde alguns instantes.",
                    status=status_str or "RESOURCE_EXHAUSTED",
                )
            elif 400 <= e.code < 500:
                raise ClientError(code=e.code, message=err_msg, status=status_str)
            elif 500 <= e.code < 600:
                raise ServerError(
                    code=e.code,
                    message="Serviço do Gemini temporariamente indisponível ou sobrecarregado (5xx).",
                    status=status_str or "UNAVAILABLE",
                )
            else:
                raise APIError(code=e.code, message=err_msg, status=status_str)

        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            raise ConnectionError(
                "Falha de conexão com a API do Gemini. Verifique sua conexão com a internet."
            ) from e

    def _parse_model_json(self, raw_response: str) -> CoachResponse:
        """Decodifica a resposta JSON do modelo e constrói o CoachResponse."""
        if not raw_response or not raw_response.strip():
            raise ValueError("Resposta vazia retornada pela API.")

        data = json.loads(raw_response)
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Nenhum candidato retornado pelo modelo.")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or not parts[0].get("text"):
            raise ValueError("Conteúdo de texto ausente na resposta do modelo.")

        text_content = parts[0]["text"].strip()
        parsed = json.loads(text_content)

        reply = parsed.get("reply", "").strip()
        if not reply:
            reply = "I understand what you mean. Could you tell me more about that?"

        error_data = parsed.get("error_detected")
        error_detail: Optional[ErrorDetail] = None

        if error_data and isinstance(error_data, dict):
            raw_cat = str(error_data.get("category", "")).strip().lower()
            category = raw_cat if raw_cat in VALID_CATEGORIES else "other"
            original = str(error_data.get("original", "")).strip()
            corrected = str(error_data.get("corrected", "")).strip()

            if original and corrected:
                error_detail = ErrorDetail(category=category, original=original, corrected=corrected)

        return CoachResponse(reply=reply, error_detected=error_detail)

    def send_message(self, student_text: str, session_id: int) -> CoachResponse:
        """Envia a fala do aluno, detecta erros e grava no banco de dados de forma resiliente."""
        student_text = student_text.strip()
        if not student_text:
            return CoachResponse(
                reply="I'm here! What would you like to talk about today?",
                error_detected=None,
            )

        # 1. Recupera contexto de erros (para detecção de reincidência)
        last_error = get_last_error(session_id, conn=self.connection)
        last_cat = last_error["category"] if last_error else None
        top_errors = get_top_errors(limit=3, conn=self.connection)

        # 2. Constrói o System Prompt contextual
        system_prompt = build_system_prompt(last_error_category=last_cat, frequent_errors=top_errors)

        # 3. Adiciona a mensagem do aluno ao histórico de turnos
        user_turn = {"role": "user", "parts": [{"text": student_text}]}
        request_contents = list(self.history) + [user_turn]

        # 4. Chamada à API com 1 tentativa de repetição (retry) para resposta vazia, JSON inválido ou falha transitória
        response_obj: Optional[CoachResponse] = None
        last_exception: Optional[Exception] = None

        for attempt in range(2):
            try:
                raw_json = self._call_gemini_endpoint(system_prompt, request_contents)
                response_obj = self._parse_model_json(raw_json)
                break
            except (ValueError, json.JSONDecodeError, ConnectionError) as e:
                last_exception = e
                continue
            except (ClientError, ServerError, APIError):
                raise

        # Se após 2 tentativas a falha persistir
        if response_obj is None:
            if isinstance(last_exception, ConnectionError):
                raise last_exception
            response_obj = CoachResponse(
                reply="That makes sense! Could you tell me a little bit more about that in English?",
                error_detected=None,
            )

        # 5. Atualiza o histórico local da conversa
        self.history.append(user_turn)
        self.history.append({
            "role": "model",
            "parts": [{"text": response_obj.reply}]
        })

        # 6. Grava mensagens e erro detectado na base de dados (real ou temporária)
        add_message(session_id, "student", student_text, conn=self.connection)
        add_message(session_id, "coach", response_obj.reply, conn=self.connection)

        if response_obj.error_detected:
            add_error(
                session_id=session_id,
                category=response_obj.error_detected.category,
                original=response_obj.error_detected.original,
                corrected=response_obj.error_detected.corrected,
                conn=self.connection,
            )

        return response_obj
