# Plano de Implementação - English Speaking Coach (v3)

## 1. Visão Geral e Estratégia

Este documento orienta o desenvolvimento passo a passo do **English Speaking Coach**, um tutor conversacional inteligente baseado na API do Google Gemini, voltado para estudantes brasileiros de nível A2–B1. O projeto é executado inteiramente na raiz `F:\Agent\`, sem subpastas extras, dividido em três fases evolutivas:

```mermaid
flowchart LR
    Fase1["Fase 1: CLI Texto<br>(Gemini + SQLite + CLI)"] --> Fase2["Fase 2: Áudio Nativo<br>(Gemini Live API)"]
    Fase2 --> Fase3["Fase 3: Interface Web<br>(Streamlit + Dashboard)"]
```

---

## 2. Estrutura de Diretórios do Projeto

```text
F:\Agent\
├── .venv/                         # Ambiente virtual Python (3.11+)
├── .git/                          # Controle de versão Git
├── .gitignore                     # Ignora .venv, .env, data/
├── .env.example                   # Modelo de configuração (GEMINI_API_KEY, GEMINI_MODEL)
├── .env                           # Chave de API local (nunca versionada nem exibida)
├── requirements.txt               # Dependências externas do projeto
├── README.md                      # Documentação de introdução, instalação e execução
├── english-speaking-coach-specification-v1.md # Especificação v1 original (preservada)
│
├── docs/                          # Documentação técnica e pedagógica
│   ├── ESPECIFICACAO.md           # Especificação v3 consolidada (100% em inglês)
│   ├── PLANO.md                   # Este plano de implementação
│   ├── ARQUITETURA.md             # Desenho de arquitetura e fluxo de dados (futuro)
│   ├── PROMPTS.md                 # Versões e calibração dos prompts
│   └── DIARIO.md                  # Diário de bordo atualizado ao fim de cada etapa
│
├── data/                          # Dados locais da aplicação (ignorado no git)
│   └── coach.db                   # Banco de dados relacional SQLite
│
└── src/                           # Código-fonte modular
    ├── __init__.py
    ├── main.py                    # Ponto de entrada do CLI (loop interativo no terminal)
    ├── config.py                  # Leitura segura de .env e caminhos do projeto
    ├── agent/                     # Integração com a API do Google Gemini
    │   ├── __init__.py
    │   ├── coach.py               # Orquestrador do agente e processamento de turnos
    │   └── prompts.py             # System prompt e esquema de resposta estruturada
    └── storage/                   # Camada de banco de dados SQLite
        ├── __init__.py
        ├── database.py            # Inicialização de conexão e criação de tabelas
        └── repository.py          # Operações de CRUD (sessões, mensagens, erros)
```

---

## 3. Requisitos de Ambiente e Stack Técnica

- **Ambiente Python**: Python 3.11 ou superior.
- **Modelo Gemini**:
  - `GEMINI_MODEL`: configurável via `.env` (padrão oficial ativo: `gemini-2.5-flash`).
  - Chamada à API com resiliência a timeouts, retries automáticos e tratamento de erros.
- **Armazenamento**: SQLite nativo (`sqlite3`), arquivo local em `data/coach.db`.
- **Política de Idioma Estrita**: 100% em inglês, sem suporte ou respostas em português sob nenhuma circunstância.
  - Se o aluno escrever em português, o coach compreende a mensagem e responde inteiramente em inglês, indicando como dizer aquilo em inglês (*"You could say: '...'"*).
  - Em erros reincidentes, explica em inglês mais simples com exemplo curto.
- **Privacidade & Segurança**:
  - Arquivo `.env` **nunca deve ser lido, impresso nem commitado**.
  - Pasta `data/` protegida no `.gitignore`.

---

## 4. Arquitetura de Dados (SQLite)

O armazenamento persistente utiliza o banco de dados nativo **SQLite** (`data/coach.db`), operado pelo módulo padrão `sqlite3` do Python.

### 4.1. Esquema Relacional (3 Tabelas)

```mermaid
erDiagram
    SESSIONS ||--o{ MESSAGES : contains
    SESSIONS ||--o{ ERRORS : tracks

    SESSIONS {
        INTEGER id PK
        TEXT started_at
        TEXT ended_at
        TEXT topic
    }

    MESSAGES {
        INTEGER id PK
        INTEGER session_id FK
        TEXT role
        TEXT text
        TEXT created_at
    }

    ERRORS {
        INTEGER id PK
        INTEGER session_id FK
        TEXT category
        TEXT original
        TEXT corrected
        TEXT created_at
    }
```

1. **`sessions`**: Registra as sessões de estudo (`id`, `started_at`, `ended_at`, `topic`).
2. **`messages`**: Armazena o diálogo turno a turno (`student` e `coach`).
3. **`errors`**: Registra cada erro identificado. Categorias fixas e padronizadas:
   - `past_tense`, `present_tense`, `preposition`, `article`, `word_order`, `agreement`, `vocabulary`, `other`.

---

## 5. Dinâmica Pedagógica, Detecção de Reincidência e Sem Limite de Tempo

- **Sem limite artificial de tempo ou de frases**: O coach responde de forma natural e proporcional à fala do aluno, focando em fluidez e clareza.
- **Regra de 1 Erro por Turno**: Corrige no máximo 1 erro principal por interação, priorizando a compreensão da ideia.
- **Tratamento de Reincidência**:
  - O sistema envia no prompt a categoria do erro do turno anterior e os erros mais frequentes do histórico.
  - Se o erro da mesma regra se repetir em turnos consecutivos, o coach explica de outro jeito, em **inglês ainda mais simples e com um exemplo curto**, sem usar português.
- **Saída Estruturada**:
  - `reply`: A resposta conversacional vista pelo aluno (100% em inglês).
  - `error_detected`: Objeto com `category`, `original` e `corrected`. **Preenchido somente quando o `reply` de fato corrigir o erro**; caso contrário, deve ser `null`.

---

## 6. Tratamento Robusto de Erros

1. **Chave de API Ausente**:
   - Validação na inicialização (`src/config.py`).
   - Se `GEMINI_API_KEY` não estiver definida, o programa orienta em português sobre como configurar o `.env` com base no `.env.example` e encerra com código amigável sem lançar stack trace cru.
2. **Falha de Rede e Conectividade**:
   - Tratamento de exceções com retry automático e mensagem clara para tentar novamente sem perder a sessão.
3. **Limite de Taxa / Cota da API (Rate Limit 429)**:
   - Tratamento de `ClientError` (código HTTP 429 / `RESOURCE_EXHAUSTED`), alertando o aluno de forma compreensível.
4. **Encerramento por Teclado (`Ctrl+C` / `KeyboardInterrupt`)**:
   - Captura graciosa de interrupção em qualquer ponto do loop conversacional.
   - Atualização imediata do campo `ended_at` da sessão atual no SQLite antes do encerramento.

---

## 7. Detalhamento das Fases

### Fase 1: CLI em Texto e Persistência SQLite

#### Etapa 1.1: Dependências, Configuração e Ambiente
- Criar `requirements.txt`: `google-genai`, `python-dotenv`, `pydantic`.
- Criar `.env.example`: `GEMINI_API_KEY` e `GEMINI_MODEL=gemini-2.5-flash`.
- Atualizar `.gitignore` protegendo `.env` e `data/`.
- Implementar `src/config.py`: carregamento seguro de variáveis e validação.

#### Etapa 1.2: Camada de Dados SQLite (`src/storage/`)
- Implementar `src/storage/database.py` e `src/storage/repository.py`.
- Suporte a injeção de conexão para testes com banco temporário em memória (`:memory:`).

#### Etapa 1.3: Agente Coach e Prompts (`src/agent/`)
- Implementar `src/agent/prompts.py`:
  - System prompt 100% em inglês estrito.
  - Categorias de erro fixas (`past_tense`, `present_tense`, `preposition`, `article`, `word_order`, `agreement`, `vocabulary`, `other`).
  - Injeção contextual do erro anterior e erros frequentes.
- Implementar `src/agent/coach.py`:
  - Saída estruturada (`reply` + `error_detected`).
  - Hierarquia de exceções (`APIError`, `ClientError`, `ServerError`).
  - Retry automático em resposta vazia ou JSON inválido.

#### Etapa 1.4: Interface CLI (`src/main.py`)
- Loop interativo no terminal:
  - Saudação inicial amigável em inglês simples estimulando a prática.
  - Comandos: `/help`, `/errors`, `/exit`.
  - Captura graciosa de `Ctrl+C` com encerramento de sessão gravando `ended_at`.

#### Etapa 1.5: Testes e Validação Pedagógica
- Testes com banco em memória cobrindo erros em inglês, frases corretas, reincidência e entradas em português.

---

### Fase 2: Integração de Áudio Nativo (Speech-to-Speech) - ✅ CONCLUÍDA
- Conexão bidirecional assíncrona com a **Gemini Live API** via WebSockets no FastAPI.
- Streaming contínuo de áudio PCM (16 kHz entrada / 24 kHz saída).
- Interface web Sci-Fi interativa em arquivo único (`src/web/static/index.html`) com controle único `START / STOP` e indicador de pensamento (`● ● ●`).
- Jitter buffer de áudio e enfileiramento sequencial eliminando sobreposição de pacotes.
- Persistência automática das mensagens e sessões de voz no banco SQLite.
- Regras pedagógicas de acompanhamento do fio condutor (*thread continuity*) e tratamento do *"mais"* brasileiro.

---

### Fase 3: Multi-dispositivo, Rede Local e Validação Mobile - 🔄 EM ANDAMENTO

#### 3.1. Conectividade de Rede Local e WSL2 (✅ Concluída)
- Resolução do isolamento de rede do WSL2 através de `netsh interface portproxy` no Windows.
- Liberação de regras de entrada no Windows Defender Firewall (porta 8000 TCP).
- Uvicorn configurado em `0.0.0.0`, permitindo conexões diretas via endereço IP local da máquina.

#### 3.2. Validação em Dispositivo Móvel Real (Android) (🔄 Em Andamento)
- **Status Positivo**:
  - Acesso ao frontend web Sci-Fi via Wi-Fi validado com sucesso a partir de smartphone Android real.
  - Conexão WebSocket bidirecional estabelecida normalmente.
  - Backend FastAPI no WSL2 responsivo e integrado ao SQLite.
  - Gemini Live API operacional durante os testes móveis.
- **Bloqueador Atual (Em Investigação)**:
  - Falha na chamada da API de captura de microfone no Android: `"Cannot read properties of undefined (reading 'getUserMedia')"`.
  - Diagnóstico: Exigência de **Contexto Seguro (*Secure Context*)** pelo navegador Chromium móvel, que desativa `navigator.mediaDevices` quando acessado via protocolo HTTP por IP de rede local.
- **Próxima Etapa Prioritária**:
  - Implementar terminação TLS/HTTPS segura (certificados locais com `mkcert` ou túnel HTTPS seguro) para restaurar a API `getUserMedia` no Android e validar a conversação completa speech-to-speech em dispositivo móvel.

---

## 8. Status e Critérios de Conclusão

1. **Fase 1 (CLI & Persistência)**: ✅ 100% Concluída e testada.
2. **Fase 2 (Voz em Tempo Real & Web)**: ✅ 100% Concluída com Gemini Live API e UI Sci-Fi.
3. **Fase 3 (Acesso Mobile & Multi-dispositivo)**: 🔄 Acesso web e WebSocket validados no Android; resolução da captura de áudio (HTTPS / Secure Context) definida como prioridade imediata.
