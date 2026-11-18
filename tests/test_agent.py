"""Testes automatizados da Etapa 1.3 (Prompts e CoachAgent) com banco temporário em memória e imersão 100% em inglês."""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.prompts import (
    INITIAL_GREETING,
    VALID_CATEGORIES,
    build_system_prompt,
    SYSTEM_PROMPT_TEMPLATE,
    ErrorCategory,
)
from src.agent.coach import (
    CoachAgent,
    CoachResponse,
    ErrorDetail,
    APIError,
    ClientError,
    ServerError,
)
from src.storage.repository import (
    create_session,
    get_session_messages,
    get_last_error,
    get_top_errors,
)


def create_in_memory_db() -> sqlite3.Connection:
    """Cria um banco SQLite 100% em memória para não tocar no banco real."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            topic TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'coach')),
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );
    """)
    cursor.execute("""
        CREATE TABLE errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            original TEXT NOT NULL,
            corrected TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    return conn


def test_prompts():
    print("=== Testando src/agent/prompts.py (100% Inglês) ===")
    assert len(VALID_CATEGORIES) == 8
    assert "past_tense" in VALID_CATEGORIES
    assert "present_tense" in VALID_CATEGORIES
    assert "preposition" in VALID_CATEGORIES
    assert "article" in VALID_CATEGORIES
    assert "word_order" in VALID_CATEGORIES
    assert "agreement" in VALID_CATEGORIES
    assert "vocabulary" in VALID_CATEGORIES
    assert "other" in VALID_CATEGORIES

    # Verifica que não há suporte a português no prompt
    assert "STRICT 100% ENGLISH POLICY" in SYSTEM_PROMPT_TEMPLATE
    assert "Portuguese Support" not in SYSTEM_PROMPT_TEMPLATE
    assert "explanation in Portuguese" not in SYSTEM_PROMPT_TEMPLATE
    print("Garantia de 100% em inglês no System Prompt: OK")

    # Injeção sem erros prévios (last_error_category = none)
    prompt_initial = build_system_prompt(last_error_category=None, frequent_errors=None)
    assert "Last turn error category: none" in prompt_initial
    assert "Student's frequent error categories: none yet" in prompt_initial
    print("Injeção inicial com 'none': OK")

    # Injeção com histórico
    prompt_with_history = build_system_prompt(
        last_error_category="past_tense",
        frequent_errors=[{"category": "past_tense", "count": 3}, {"category": "preposition", "count": 2}],
    )
    assert "Last turn error category: past_tense" in prompt_with_history
    assert "past_tense (3x), preposition (2x)" in prompt_with_history
    print("Injeção com histórico de erros: OK")


def test_parsing_and_error_handling():
    print("\n=== Testando parsing de JSON e Tratamento de Exceções ===")
    agent = CoachAgent(api_key="test_key", model="gemini-2.5-flash")

    # 1. Parsing com erro detectado
    sample_json = json.dumps({
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "reply": "That sounds nice! A natural way to say it is: 'I went to the beach.' What did you do there?",
                        "error_detected": {
                            "category": "past_tense",
                            "original": "I go to beach",
                            "corrected": "I went to the beach"
                        }
                    })
                }]
            }
        }]
    })

    resp = agent._parse_model_json(sample_json)
    assert "I went to the beach" in resp.reply
    assert resp.error_detected is not None
    assert resp.error_detected.category == "past_tense"
    assert resp.error_detected.original == "I go to beach"
    print("Parsing com erro detectado: OK")

    # 2. Parsing sem erro (error_detected = null)
    sample_no_error = json.dumps({
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "reply": "Great job! What else did you do yesterday?",
                        "error_detected": None
                    })
                }]
            }
        }]
    })
    resp_no_error = agent._parse_model_json(sample_no_error)
    assert resp_no_error.error_detected is None
    print("Parsing sem erro (error_detected = null): OK")

    # 3. Categoria inválida deve cair em 'other'
    sample_invalid_cat = json.dumps({
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "reply": "Nice sentence!",
                        "error_detected": {
                            "category": "unknown_cat",
                            "original": "foo",
                            "corrected": "bar"
                        }
                    })
                }]
            }
        }]
    })
    resp_invalid = agent._parse_model_json(sample_invalid_cat)
    assert resp_invalid.error_detected.category == "other"
    print("Fallback de categoria inválida para 'other': OK")

    # 4. Hierarquia de Exceções
    client_err = ClientError(429, "Rate limit exceeded", "RESOURCE_EXHAUSTED")
    assert isinstance(client_err, APIError)
    assert client_err.code == 429

    server_err = ServerError(503, "Service unavailable", "UNAVAILABLE")
    assert isinstance(server_err, APIError)
    assert server_err.code == 503
    print("Hierarquia de exceções (APIError, ClientError, ServerError): OK")


def test_agent_with_live_api_and_in_memory_db():
    print("\n=== Testando CoachAgent com API Real em Banco em Memória ===")
    mem_conn = create_in_memory_db()
    session_id = create_session(topic="Live Immersion Test", conn=mem_conn)

    agent = CoachAgent(connection=mem_conn)
    assert agent.get_greeting() == INITIAL_GREETING
    print(f"Saudação inicial: {agent.get_greeting()[:40]}... OK")

    # Turno 1: Aluno comete erro em inglês
    student_msg1 = "Yesterday I go to the mall with my brother."
    response1 = agent.send_message(student_msg1, session_id=session_id)
    print(f"\n[Turno 1 - Aluno]: {student_msg1}")
    print(f"[Turno 1 - Coach]: {response1.reply}")
    assert response1.reply != ""
    if response1.error_detected:
        print(f"[Turno 1 - Erro]: {response1.error_detected.category} -> '{response1.error_detected.original}' corrigido para '{response1.error_detected.corrected}'")
        assert response1.error_detected.category in VALID_CATEGORIES

    # Turno 2: Aluno escreve em português
    student_msg2 = "Eu gosto muito de viajar para a praia nas férias."
    response2 = agent.send_message(student_msg2, session_id=session_id)
    print(f"\n[Turno 2 - Aluno em PT]: {student_msg2}")
    print(f"[Turno 2 - Coach em EN]: {response2.reply}")
    assert response2.reply != ""
    # Coach responde 100% em inglês
    palavras_pt = ["você", "pode", "dizer", "falar", "praia", "férias", "muito", "gosto"]
    for palavra in palavras_pt:
        assert palavra not in response2.reply.lower(), f"Palavra em português '{palavra}' não deveria estar na resposta do coach!"
    print("Resposta ao português foi 100% em inglês: OK")

    # Verifica persistência no banco em memória
    messages = get_session_messages(session_id, conn=mem_conn)
    assert len(messages) == 4
    assert messages[0]["role"] == "student"
    assert messages[1]["role"] == "coach"
    assert messages[2]["role"] == "student"
    assert messages[3]["role"] == "coach"
    print("\n4 Mensagens registradas no banco em memória com sucesso.")

    mem_conn.close()
    print("Banco em memória fechado com sucesso, sem tocar em data/coach.db.")


if __name__ == "__main__":
    test_prompts()
    test_parsing_and_error_handling()
    test_agent_with_live_api_and_in_memory_db()
    print("\n=== Todos os testes foram concluídos com 100% de sucesso! ===")
