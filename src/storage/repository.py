"""Repositório de operações CRUD e agregações analíticas no SQLite."""

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .database import get_connection


def _current_timestamp() -> str:
    """Gera o timestamp ISO 8601 atual em UTC."""
    return datetime.now(timezone.utc).isoformat()


def _get_active_conn(conn: Optional[sqlite3.Connection]) -> sqlite3.Connection:
    """Retorna a conexão injetada ou abre a padrão."""
    if conn is not None:
        return conn
    return get_connection()


def create_session(topic: str = "General Conversation", conn: Optional[sqlite3.Connection] = None) -> int:
    """Cria uma nova sessão no banco de dados e retorna o seu ID."""
    started_at = _current_timestamp()
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (started_at, topic) VALUES (?, ?);",
        (started_at, topic),
    )
    if conn is None:
        active_conn.commit()
        active_conn.close()
    else:
        active_conn.commit()
    return cursor.lastrowid


def end_session(session_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    """Registra o timestamp de encerramento da sessão."""
    ended_at = _current_timestamp()
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ?;",
        (ended_at, session_id),
    )
    if conn is None:
        active_conn.commit()
        active_conn.close()
    else:
        active_conn.commit()


def get_session(session_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """Recupera os dados de uma sessão específica."""
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        "SELECT id, started_at, ended_at, topic FROM sessions WHERE id = ?;",
        (session_id,),
    )
    row = cursor.fetchone()
    if conn is None:
        active_conn.close()
    return dict(row) if row else None


def add_message(session_id: int, role: str, text: str, conn: Optional[sqlite3.Connection] = None) -> int:
    """Grava uma mensagem ('student' ou 'coach') associada a uma sessão."""
    if role not in ("student", "coach"):
        raise ValueError(f"Papel inválido '{role}'. Deve ser 'student' ou 'coach'.")
    created_at = _current_timestamp()
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (session_id, role, text, created_at)
        VALUES (?, ?, ?, ?);
        """,
        (session_id, role, text, created_at),
    )
    if conn is None:
        active_conn.commit()
        active_conn.close()
    else:
        active_conn.commit()
    return cursor.lastrowid


def get_session_messages(session_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retorna todas as mensagens da sessão em ordem cronológica."""
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        SELECT id, session_id, role, text, created_at
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC;
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    if conn is None:
        active_conn.close()
    return [dict(row) for row in rows]


def add_error(
    session_id: int,
    category: str,
    original: str,
    corrected: str,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Registra um erro detectado no turno da conversa."""
    created_at = _current_timestamp()
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        INSERT INTO errors (session_id, category, original, corrected, created_at)
        VALUES (?, ?, ?, ?, ?);
        """,
        (session_id, category.strip().lower(), original.strip(), corrected.strip(), created_at),
    )
    if conn is None:
        active_conn.commit()
        active_conn.close()
    else:
        active_conn.commit()
    return cursor.lastrowid


def get_top_errors(limit: int = 3, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retorna as categorias de erros mais frequentes e suas contagens agregadas."""
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        SELECT category, COUNT(*) as count
        FROM errors
        GROUP BY category
        ORDER BY count DESC, category ASC
        LIMIT ?;
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    if conn is None:
        active_conn.close()
    return [dict(row) for row in rows]


def get_session_errors(session_id: int, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retorna todos os erros registrados na sessão atual."""
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        SELECT id, session_id, category, original, corrected, created_at
        FROM errors
        WHERE session_id = ?
        ORDER BY id ASC;
        """,
        (session_id,),
    )
    rows = cursor.fetchall()
    if conn is None:
        active_conn.close()
    return [dict(row) for row in rows]


def get_last_error(session_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """Retorna o último erro registrado na sessão atual, se houver."""
    active_conn = _get_active_conn(conn)
    cursor = active_conn.cursor()
    cursor.execute(
        """
        SELECT id, session_id, category, original, corrected, created_at
        FROM errors
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT 1;
        """,
        (session_id,),
    )
    row = cursor.fetchone()
    if conn is None:
        active_conn.close()
    return dict(row) if row else None
