"""Camada de persistência e armazenamento em SQLite."""

from .database import get_connection, init_db
from .repository import (
    create_session,
    end_session,
    add_message,
    add_error,
    get_top_errors,
    get_last_error,
    get_session_errors,
    get_session_messages,
    get_session,
)

__all__ = [
    "get_connection",
    "init_db",
    "create_session",
    "end_session",
    "add_message",
    "add_error",
    "get_top_errors",
    "get_last_error",
    "get_session_errors",
    "get_session_messages",
    "get_session",
]
