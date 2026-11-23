"""Configurações e gerenciamento de ambiente para o English Speaking Coach."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Diretório raiz do projeto (F:\Agent)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis do arquivo .env (sem imprimir ou expor valores)
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Caminhos do banco de dados e arquivos locais
DATA_DIR = ROOT_DIR / "data"
DATABASE_PATH = DATA_DIR / "coach.db"

# Modelo oficial ativo no Google AI Studio (alta disponibilidade e baixa latência)
DEFAULT_MODEL = "gemini-2.5-flash"

# Configurações para a Gemini Live API (áudio bidirecional em tempo real)
DEFAULT_LIVE_MODEL = "gemini-3.8-live"
DEFAULT_API_VERSION = "v1beta"
DEFAULT_VOICE_NAME = "Puck"


def get_gemini_api_key() -> str:
    """Retorna a chave de API do Gemini após validar que ela existe e não é o placeholder.
    
    Nunca imprime nem expõe o valor da chave.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "sua_chave_aqui":
        raise ValueError(
            "Chave de API do Gemini não configurada!\n"
            "Por favor, verifique o arquivo .env na raiz do projeto com base no .env.example "
            "e defina uma GEMINI_API_KEY válida."
        )
    return key


def get_gemini_model() -> str:
    """Retorna o nome do modelo do Gemini configurado ou o padrão oficial."""
    model = os.getenv("GEMINI_MODEL", "").strip()
    return model if model else DEFAULT_MODEL


def get_gemini_live_model() -> str:
    """Retorna o modelo configurado para a Gemini Live API (padrão: gemini-3.8-live)."""
    live_model = os.getenv("GEMINI_LIVE_MODEL", "").strip()
    return live_model if live_model else DEFAULT_LIVE_MODEL


def get_gemini_api_version() -> str:
    """Retorna a versão da API configurada para a Live API (padrão: v1beta)."""
    api_version = os.getenv("GEMINI_API_VERSION", "").strip()
    return api_version if api_version else DEFAULT_API_VERSION


def get_gemini_voice_name() -> str:
    """Retorna a voz configurada para a Live API (padrão: Puck)."""
    voice = os.getenv("GEMINI_VOICE_NAME", "").strip()
    return voice if voice else DEFAULT_VOICE_NAME

