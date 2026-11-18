"""Módulo do agente e prompts do English Speaking Coach."""

from .prompts import ErrorCategory, VALID_CATEGORIES, build_system_prompt, INITIAL_GREETING
from .coach import CoachAgent, CoachResponse, ErrorDetail, APIError, ClientError, ServerError

__all__ = [
    "ErrorCategory",
    "VALID_CATEGORIES",
    "build_system_prompt",
    "INITIAL_GREETING",
    "CoachAgent",
    "CoachResponse",
    "ErrorDetail",
    "APIError",
    "ClientError",
    "ServerError",
]
