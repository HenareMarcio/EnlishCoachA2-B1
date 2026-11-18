"""Testes automatizados para a camada de configuração e armazenamento SQLite (Etapas 1.1 e 1.2)."""

import os
import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_gemini_model, DATABASE_PATH, DATA_DIR
from src.storage import (
    init_db,
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


def run_tests():
    print("=== Testando src/config.py ===")
    model = get_gemini_model()
    print(f"Modelo configurado: {model}")
    assert model != "", "Modelo não pode ser vazio"

    print("\n=== Testando src/storage (SQLite) ===")
    init_db()
    assert DATABASE_PATH.exists(), f"Banco {DATABASE_PATH} deveria existir"
    print(f"Banco SQLite inicializado em: {DATABASE_PATH}")

    # Criação de sessão
    session_id = create_session(topic="English Conversation Test")
    print(f"Sessão criada com ID: {session_id}")
    assert session_id > 0, "ID da sessão deve ser maior que 0"

    # Inserção de mensagens
    msg1_id = add_message(session_id, "student", "I go to beach yesterday.")
    msg2_id = add_message(session_id, "coach", "That sounds fun! What did you do at the beach?")
    assert msg1_id > 0 and msg2_id > 0, "IDs de mensagens válidos"

    msgs = get_session_messages(session_id)
    assert len(msgs) == 2, f"Esperava 2 mensagens, obteve {len(msgs)}"
    assert msgs[0]["role"] == "student"
    assert msgs[1]["role"] == "coach"
    print(f"Mensagens gravadas e recuperadas: {len(msgs)} mensagens OK")

    # Registro de erros
    err1_id = add_error(session_id, "past_tense", "I go", "I went")
    err2_id = add_error(session_id, "preposition", "at Monday", "on Monday")
    err3_id = add_error(session_id, "past_tense", "I see him", "I saw him")
    assert err1_id > 0 and err2_id > 0 and err3_id > 0

    # Teste de erros da sessão
    session_errors = get_session_errors(session_id)
    assert len(session_errors) == 3, f"Esperava 3 erros, obteve {len(session_errors)}"
    print(f"Erros da sessão recuperados: {len(session_errors)} erros OK")

    # Teste de último erro
    last_err = get_last_error(session_id)
    assert last_err is not None
    assert last_err["category"] == "past_tense"
    assert last_err["original"] == "I see him"
    print(f"Último erro detectado: {last_err['category']} ('{last_err['original']}') OK")

    # Teste de agregação de erros frequentes
    top_errors = get_top_errors(limit=3)
    assert len(top_errors) >= 2
    past_tense_entry = next((e for e in top_errors if e["category"] == "past_tense"), None)
    assert past_tense_entry is not None and past_tense_entry["count"] >= 2
    print(f"Top erros agregados via SQL: {top_errors} OK")

    # Encerramento de sessão
    end_session(session_id)
    session_data = get_session(session_id)
    assert session_data["ended_at"] is not None
    print(f"Sessão finalizada com ended_at: {session_data['ended_at']} OK")

    print("\nTodos os testes das Etapas 1.1 e 1.2 passaram com 100% de sucesso!")


if __name__ == "__main__":
    run_tests()
