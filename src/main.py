"""Ponto de entrada do English Speaking Coach (CLI interativo)."""

import sys
from pathlib import Path
from typing import Optional

# Garante que a raiz do projeto esteja no sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_gemini_api_key, get_gemini_model
from src.storage import (
    init_db,
    create_session,
    end_session,
    get_session_errors,
    get_top_errors,
)
from src.agent.coach import (
    CoachAgent,
    APIError,
    ClientError,
    ServerError,
)


def print_banner(model_name: str) -> None:
    """Exibe o cabeçalho inicial do CLI com instruções de uso."""
    print("=" * 62)
    print("                ENGLISH SPEAKING COACH (CLI)               ")
    print("        Practice your English in a supportive immersion!   ")
    print("=" * 62)
    print(f"Active Model: {model_name}")
    print("Commands:")
    print("  /help   - Show available commands")
    print("  /errors - View errors detected during this session")
    print("  /exit   - End the practice session")
    print("-" * 62)


def print_help() -> None:
    """Exibe o guia de comandos do CLI."""
    print("\n--- CLI Commands ---")
    print("  /help   - Display this guide")
    print("  /errors - Display errors detected and corrected in this session")
    print("  /exit   - Save and exit the conversation (or /quit)")
    print("Just type any sentence in English to chat with the Coach!\n")


def print_session_errors(session_id: int) -> None:
    """Exibe o relatório dos erros detectados na sessão atual e histórico geral."""
    session_errors = get_session_errors(session_id)
    top_errors = get_top_errors(limit=5)

    print("\n" + "=" * 50)
    print("              SESSION ERROR REPORT                ")
    print("=" * 50)

    if not session_errors:
        print("No errors detected in this session yet. Great job! Keep going! 🎉")
    else:
        print(f"Errors detected in this session ({len(session_errors)}):")
        for i, err in enumerate(session_errors, 1):
            category = err.get("category", "other")
            original = err.get("original", "")
            corrected = err.get("corrected", "")
            print(f"  {i}. [{category}] \"{original}\" ➔ \"{corrected}\"")

    if top_errors:
        print("\nTop Recurring Error Categories (Overall History):")
        for item in top_errors:
            cat = item.get("category", "")
            count = item.get("count", 0)
            print(f"  • {cat}: {count}x")

    print("=" * 50 + "\n")


def main() -> None:
    """Loop principal de execução do terminal."""
    # 1. Validação de inicialização da chave de API
    try:
        get_gemini_api_key()
    except ValueError as e:
        print("\n" + "!" * 62)
        print("[ERRO DE CONFIGURAÇÃO]")
        print(str(e))
        print("!" * 62 + "\n")
        sys.exit(1)

    model_name = get_gemini_model()

    # 2. Inicialização do banco de dados SQLite
    try:
        init_db()
    except Exception as e:
        print(f"\n[ERRO] Falha ao inicializar banco de dados SQLite: {e}\n")
        sys.exit(1)

    # 3. Criação de sessão de conversação
    session_id: Optional[int] = None
    try:
        session_id = create_session(topic="English Speaking Practice")
    except Exception as e:
        print(f"\n[ERRO] Falha ao criar sessão de prática: {e}\n")
        sys.exit(1)

    # 4. Inicialização do Agente
    agent = CoachAgent(model=model_name)

    # 5. Apresentação inicial
    print_banner(model_name)
    print(f"\nCoach: {agent.get_greeting()}\n")

    # 6. Loop Interativo
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nSession interrupted. Ending session...")
                break

            if not user_input:
                continue

            # Comandos de controle
            command = user_input.lower()
            if command in ("/exit", "/quit"):
                print("\nCoach: Goodbye! Thanks for practicing English today. Keep it up! See you soon!\n")
                break

            if command == "/help":
                print_help()
                continue

            if command == "/errors":
                print_session_errors(session_id)
                continue

            # Processamento do turno de conversa com o Coach
            try:
                response = agent.send_message(user_input, session_id=session_id)
                print(f"\nCoach: {response.reply}\n")

            except ClientError as e:
                if e.code == 429:
                    print("\n[Notice] Rate limit reached (Quota 429). Please wait a few seconds and try again.\n")
                else:
                    print(f"\n[Notice] API Client Error ({e.code}): {e.message}\n")

            except ServerError as e:
                print(f"\n[Notice] Gemini service temporarily overloaded ({e.code}). Please try again in a few moments.\n")

            except ConnectionError:
                print("\n[Notice] Connection issue with Gemini API. Check your internet connection and try again.\n")

            except APIError as e:
                print(f"\n[Notice] API Error ({e.code}): {e.message}\n")

            except Exception as e:
                print(f"\n[Notice] An unexpected error occurred: {e}\n")

    finally:
        # Encerramento gracioso da sessão no banco de dados
        if session_id is not None:
            try:
                end_session(session_id)
            except Exception:
                pass


if __name__ == "__main__":
    main()
