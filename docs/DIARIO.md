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

---

## [2026-11-18] - Conclusão da Fase 2: Servidor FastAPI e Gemini Live API (Áudio Bidirecional)

- **Atividades e Implementações**:
  - Adição de `fastapi` e `uvicorn` ao [**`requirements.txt`**](file:///f:/Agent/requirements.txt).
  - Atualização de [**`src/config.py`**](file:///f:/Agent/src/config.py) e [**`.env.example`**](file:///f:/Agent/.env.example) com suporte a `GEMINI_LIVE_MODEL` (padrão: `gemini-3.8-live`) e `GEMINI_API_VERSION` (padrão: `v1beta`).
  - Criação do prompt adaptado para voz em [**`src/agent/prompts.py`**](file:///f:/Agent/src/agent/prompts.py) (`VOICE_SYSTEM_PROMPT` e `get_voice_system_prompt()`), mantendo 80% conversa, 20% correção gentil, 1 erro por turno, imersão 100% em inglês e respostas concisas de 1 a 3 frases.
  - Implementação do servidor FastAPI em [**`src/web/server.py`**](file:///f:/Agent/src/web/server.py):
    - Endpoint WebSocket `/ws` para streaming bidirecional de áudio PCM.
    - Conexão assíncrona com `google-genai` Live API (`types.LiveConnectConfig` com `AUDIO`, transcrição de entrada/saída ativadas e `http_options`).
    - Chave da API protegida exclusivamente no servidor.
    - Persistência automática das mensagens de cada turno no SQLite via [**`src/storage/repository.py`**](file:///f:/Agent/src/storage/repository.py).
    - Tratamento de interrupção em tempo real (barge-in) e erros de cota (429 Rate Limit) com mensagens claras.
  - Criação da interface em arquivo único [**`src/web/static/index.html`**](file:///f:/Agent/src/web/static/index.html):
    - Captura de áudio do microfone com `getUserMedia` e `AudioWorklet` (resampling e conversão para PCM 16-bit 16 kHz).
    - Reprodução contínua e sem cortes de áudio PCM 24 kHz recebido do Gemini.
    - Botões Iniciar e Parar com controle de ciclo de vida.
    - Exibição em tempo real das transcrições do aluno e do coach, com histórico visual sincronizado.

---

## [2026-11-19] - Refinamento e Resiliência da Live API no Servidor Web (`src/web/server.py`)

- **Correções Aplicadas**:
  - **(a) Parâmetro de envio**: substituído `send_realtime_input(media=...)` por `send_realtime_input(audio=types.Blob(data=pcm_data, mime_type="audio/pcm;rate=16000"))`.
  - **(b) Continuidade multiturmo**: `live_session.receive()` envolvido em um laço `while True:`, garantindo que a sessão não finalize prematuramente após o primeiro turno de fala.
  - **(c) Desconexão limpa do navegador**: adicionada checagem explícita `if msg.get("type") == "websocket.disconnect": break` para prevenir erros do Starlette de tentativa de leitura após fechamento.
  - **(d) Telemetria e logs em tempo real**:
    - Log do 1º bloco de áudio do navegador e contador acumulado de bytes a cada 50 blocos.
    - Log do 1º chunk de áudio gerado pelo Gemini.
    - Log imediato de cada transcrição parcial de entrada (aluno) e saída (coach) sem aguardar o fim do turno.

---

## [2026-11-19] - Calibração Pedagógica: Pacing Lento, Brevidade Radical e Repetição

- **Problemas Endereçados**:
  - Respostas longas demais do coach (monólogos que roubavam o tempo de fala do aluno).
  - Áudio gerado em velocidade excessiva para o nível A2–B1.
- **Ajustes no Prompt de Voz (`VOICE_SYSTEM_PROMPT` em `src/agent/prompts.py`)**:
  - **Cadência de fala (*Pacing*)**: Instrução mandatória para falar de forma calma, lenta (~110–120 palavras por minuto) e com enunciação clara e micro-pausas respiratórias entre frases.
  - **Brevidade Radical**: Teto estrito de 1 a 2 frases curtas (máximo 25 palavras no total por turno) e a regra de falar menos que o aluno.
  - **Estrutura por Turno**: Reação curta (3-5 palavras) + correção sutil (se indispensável) + uma única pergunta aberta de seguimento.
  - **Protocolo de Repetição e Ajuste de Nível**: Se o aluno pedir repetição (*"What?", "Can you repeat?"*), o coach repete a mesma frase mais devagar; se o aluno travar, simplifica para vocabulário A2 imediato.
