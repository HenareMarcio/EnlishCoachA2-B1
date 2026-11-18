# Diário de Bordo - English Speaking Coach

Este documento registra as atividades concluídas, decisões de arquitetura e problemas solucionados ao final de cada etapa do projeto.

---

## [2026-11-16] - Planejamento e Arquitetura Inicial

- **Atividades**:
  - Leitura e análise da especificação original v1 (`english-speaking-coach-specification-v1.md`).
  - Alinhamento de requisitos com o usuário: foco em fluência A2–B1, 80% conversa e 20% correção, sem limite rígido de tempo de fala.
  - Definição da stack tecnológica oficial: Google Gemini (`google-genai`), Python 3.11+, persistência em SQLite em arquivo único (`data/coach.db`).
  - Criação da documentação viva: `docs/ESPECIFICACAO.md` e `docs/PLANO.md`.

---

## [2026-11-16] - Conclusão das Etapas 1.1 e 1.2

### Etapa 1.1: Dependências, Configuração e Ambiente
- **Arquivos criados/atualizados**:
  - `requirements.txt`: bibliotecas `google-genai`, `python-dotenv` e `pydantic`.
  - `.env.example`: modelo documentado com `GEMINI_API_KEY` e `GEMINI_MODEL=gemini-3.5-flash`.
  - `.gitignore`: proteção estrita para nunca versionar `.env`, `data/` e bancos `.db`.
  - `src/config.py`: carregamento seguro de variáveis e validação da chave sem expor dados confidenciais.

### Etapa 1.2: Camada de Armazenamento SQLite (`src/storage/`)
- **Arquivos criados**:
  - `src/storage/database.py`: inicialização automática de diretórios e criação das 3 tabelas (`sessions`, `messages`, `errors`) com integridade referencial (`PRAGMA foreign_keys = ON;`) e índices otimizados.
  - `src/storage/repository.py`:
    - Funções de ciclo de vida de sessão: `create_session`, `end_session`, `get_session`.
    - Histórico de mensagens: `add_message`, `get_session_messages`.
    - Registro e catalogação de erros: `add_error`.
    - Detecção de reincidência e análise: `get_last_error` e `get_top_errors`.
    - Suporte a injeção de conexão para testes com banco em memória (`:memory:`).

---

## [2026-11-17] - Refinamento: Imersão Estrita 100% em Inglês (Sem Português)

- **Decisão e Ajustes Aplicados**:
  - Remoção completa de qualquer menção ou suporte a português na experiência do tutor, **inclusive condicional**.
  - O tutor opera 100% em inglês sob qualquer circunstância.
  - Se o aluno escrever ou falar em português, o coach compreende a mensagem perfeitamente e responde exclusivamente em inglês, demonstrando a forma natural equivalente (*"You could say: '...'"*).
  - Em casos de reincidência no mesmo erro, o coach explica de forma alternativa, em **inglês ainda mais simples e com exemplo prático**, sem jamais recorrer ao português.
  - Eliminação de qualquer variável ou arquivo ligado a suporte em português (`config.json`, `pt_support` e comandos `/pt on` e `/pt off`).
  - Comandos do CLI mantidos: `/help`, `/errors` e `/exit`.
  - Atualização dos documentos [**`docs/ESPECIFICACAO.md`**](file:///f:/Agent/docs/ESPECIFICACAO.md), [**`docs/PLANO.md`**](file:///f:/Agent/docs/PLANO.md), [**`docs/PROMPTS.md`**](file:///f:/Agent/docs/PROMPTS.md) e do código em [**`src/agent/prompts.py`**](file:///f:/Agent/src/agent/prompts.py).
  - Execução e aprovação da suíte de testes [**`tests/test_agent.py`**](file:///f:/Agent/tests/test_agent.py) com banco temporário em memória (`:memory:`), validando que as respostas diante de frases em português são 100% em inglês.

---

## [2026-11-17] - Conclusão da Etapa 1.4: Interface CLI (`src/main.py`)

- **Atividades e Implementações**:
  - Implementação completa de [**`src/main.py`**](file:///f:/Agent/src/main.py) conectando todas as camadas (configuração, banco de dados SQLite e CoachAgent).
  - Loop interativo com exibição de banner limpo e saudação inicial amigável em inglês.
  - Comandos interativos de terminal implementados:
    - `/help`: exibe instruções claras de uso.
    - `/errors`: lista todos os erros detectados e corrigidos na sessão atual e exibe o ranking histórico de categorias frequentes.
    - `/exit` ou `/quit`: encerra a sessão com mensagem amigável de despedida.
  - Captura graciosa de interrupção por teclado (`Ctrl+C` / `KeyboardInterrupt`), finalizando a sessão e persistindo o timestamp `ended_at` no banco SQLite via bloco `finally`.
  - Tratamento resiliente de exceções (Rate limit 429, falha 5xx, timeout e perda de conexão com a internet) mantendo o loop ativo para novas tentativas.
  - Adição de `get_session_errors` em [**`src/storage/repository.py`**](file:///f:/Agent/src/storage/repository.py) e exportação em `src/storage/__init__.py`.
  - Alinhamento do modelo padrão oficial para `gemini-2.5-flash` em [**`src/config.py`**](file:///f:/Agent/src/config.py).
