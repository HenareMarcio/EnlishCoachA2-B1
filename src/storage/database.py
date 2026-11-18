"""Inicialização e gerenciamento da conexão SQLite para o English Speaking Coach."""

import sqlite3
from src.config import DATA_DIR, DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Cria e retorna uma conexão com o banco SQLite com row_factory ativado."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Cria as tabelas e índices necessários no banco SQLite caso não existam."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Tabela sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                topic TEXT
            );
        """)

        # 2. Tabela messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'coach')),
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            );
        """)

        # 3. Tabela errors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                original TEXT NOT NULL,
                corrected TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            );
        """)

        # Índices para consultas frequentes e agrupamentos
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_session ON errors(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_category ON errors(category);")

        conn.commit()
