# English Speaking Coach AI

<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" width="100" alt="English Speaking Coach Logo" />
</p>

<p align="center">
  <strong>Agente conversacional inteligente de voz em tempo real para desenvolvimento de fluência e confiança em língua inglesa.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Google%20Gemini-Live%20API-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini Live API" />
  <img src="https://img.shields.io/badge/Web%20Audio-24kHz%20PCM-00E5FF?style=for-the-badge" alt="Web Audio API" />
  <img src="https://img.shields.io/badge/SQLite-Local%20Storage-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="MIT License" />
</p>

---

## 📌 Visão Geral

O **English Speaking Coach** é uma plataforma desenvolvida para superar a maior barreira no aprendizado de inglês de estudantes brasileiros (níveis A2–B1): a **insegurança ao falar** e a escassez de prática conversacional realista.

Diferente de chatbots tradicionais baseados em turnos de texto ou avaliadores gramaticais rígidos, o coach atua como um **verdadeiro parceiro de conversa falada**:
- Comunicação bidirecional contínua de áudio em tempo real (*speech-to-speech*).
- Foco em **fluência, manutenção de assunto (*thread continuity*) e comunicação natural**.
- Correção gentil e pontual (*recasting*), sem interromper o raciocínio nem ministrar palestras teóricas.
- Imersão total em inglês com sensibilidade aos padrões de dúvida de aprendizes falantes de português.

> **Desenvolvido por:** **MHMF Technologies**

---

## 🚀 Principais Atualizações Recentes

### 1. Interface Web Sci-Fi com Glassmorphism
- **Design Futurista:** Paleta temática espacial com efeitos neon ciano (`#00e5ff`) e cartões em vidro translúcido (*glassmorphism*).
- **Controle Unificado:** Botão único inteligente `▶ START` / `■ STOP` com transições de estado visual.
- **Indicador de Pensamento:** Feedback em tempo real (`● ● ●`) durante a escuta e processamento da fala do aluno.
- **Avatar Dinâmico:** Humanoide animado flutuante para uma experiência mais acolhedora.

### 2. Motor de Voz em Tempo Real de Baixa Latência (Gemini Live API)
- **Streaming Bidirecional:** Captura de microfone via `AudioWorklet` (PCM 16 kHz) e reprodução contínua (PCM 24 kHz) sem sobreposição ou atropelo de áudio.
- **Agendamento com Jitter Buffer:** Mecanismo de enfileiramento na `Web Audio API` que garante reprodução sequencial e suave, eliminando qualquer aceleração ou sobreposição de pacotes.
- **VAD Otimizado:** Detecção natural de atividade de voz sem silêncio artificial forçado, reduzindo drasticamente o tempo de resposta (*Time-to-First-Audio*).
- **Seleção de Vozes:** Suporte flexível a vozes do Google AI Studio (`Puck`, `Aoede`, `Charon`, etc.) via configuração de ambiente.

### 3. Inteligência Pedagógica e Manutenção de Contexto
- **Parceiro vs. Chatbot:** O coach é instruído a nunca inventar perguntas aleatórias ou mudar de tema sem motivo. Ele escuta, valida o que o aluno disse e aprofunda o assunto em andamento.
- **Tratamento Inteligente de Dúvidas ("Mais"):** Identificação de expressões típicas brasileiras de pedido de repetição (*"mais"*, *"again"*, *"repeat"*, *"what?"*, *"sorry?"*, *"como?"*). O coach repara a frase em inglês mais simples e oferece alternativas claras sem trocar de assunto.
- **Rótulos Objetivos:** Diálogo estruturado no histórico entre `ME` (aluno) e `COACH`.

### 4. Arquitetura de Servidor FastAPI e Persistência
- **Lifespan Context Manager:** Gerenciamento de ciclo de vida moderno substituindo eventos depreciados.
- **Tratamento Robusto de Concorrência:** Tratamento de exceções assíncronas em segundo plano, evitando falhas silenciosas na comunicação com o WebSocket.
- **Endpoint de Saúde:** Diagnóstico rápido em `/api/health` para verificação de chaves e modelos ativos.
- **Persistência SQLite:** Histórico completo de conversações, turnos e categorias de erros persistidos localmente no banco `coach.db`.

---

## 🏛️ Arquitetura do Sistema

```
                  ┌──────────────────────────────────────────────┐
                  │          Navegador Web do Aluno              │
                  │  (AudioWorklet 16kHz + Web Audio API 24kHz)  │
                  └──────────────────────┬───────────────────────┘
                                         │ WebSocket Bidirecional
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Servidor FastAPI (Async)          │
                  │  - Roteamento e Lifecycle (Lifespan)         │
                  │  - Supervisão de Concorrência de Tarefas     │
                  │  - Verificação de Conexão e Safe Senders     │
                  └──────────────┬───────────────────────────────┘
                                 │
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│        Gemini Live API          │      │     Camada de Armazenamento     │
│   (Model: gemini-3.8-live /     │      │        (SQLite Local)           │
│    Speech-to-Speech Streaming)  │      │  - Registro de Sessões          │
│   - Transcrição Aluno & Coach   │      │  - Histórico de Turnos          │
│   - Detecção de Interrupções    │      │  - Métricas e Categorias Erros  │
└─────────────────────────────────┘      └─────────────────────────────────┘
```

---

## 📂 Estrutura do Diretório

```text
Agent/
├── data/                    # Banco de dados local SQLite (coach.db)
├── docs/                    # Documentação detalhada e registros de evolução
│   ├── ESPECIFICACAO.md
│   ├── PLANO.md
│   ├── PROMPTS.md
│   └── TROUBLESHOOTING.md
├── scripts/                 # Scripts utilitários de validação
│   └── check_live.py        # Validação de conectividade com a Live API
├── src/
│   ├── agent/               # Lógica do Agente e Prompts Pedagógicos
│   │   ├── coach.py         # Implementação do CoachAgent e parsing
│   │   └── prompts.py       # Prompts do Coach (Live Voice & CLI)
│   ├── storage/             # Camada de Dados SQLite
│   │   ├── database.py      # Conexões e schemas de tabelas
│   │   └── repository.py    # CRUD de sessões, mensagens e erros
│   ├── web/                 # Servidor Web e Interface
│   │   ├── server.py        # FastAPI, WebSocket e Gateway Gemini Live
│   │   └── static/
│   │       └── index.html   # Frontend Sci-Fi em arquivo único
│   ├── config.py            # Validação e carregamento de configurações
│   └── main.py              # Interface CLI (modo texto)
├── tests/                   # Suíte de testes automatizados com Pytest
├── .env.example             # Modelo de configuração de ambiente
├── requirements.txt         # Dependências Python do projeto
└── README.md                # Documentação técnica do projeto
```

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia | Finalidade |
|---|---|---|
| **Linguagem** | Python 3.10+ | Linguagem central do backend e lógica de controle |
| **Backend Web** | FastAPI & Uvicorn | Servidor assíncrono de alta performance com WebSockets |
| **IA de Voz** | Google GenAI SDK | Conexão com Gemini Live API (*bidiGenerateContent*) |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Interface Sci-Fi responsiva com Web Audio API e AudioWorklet |
| **Banco de Dados** | SQLite | Persistência local e segura de mensagens, sessões e erros |
| **Testes** | Pytest | Testes automatizados em memória para validação de lógica |

---

## ⚙️ Configuração e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/HenareMarcio/EnlishCoachA2-B1.git
cd EnlishCoachA2-B1
```

### 2. Configurar Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```env
# Chave oficial do Google AI Studio (https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=sua_chave_aqui

# Modelo para o modo texto (CLI)
GEMINI_MODEL=gemini-2.5-flash

# Configurações do Modo Voz em Tempo Real (Gemini Live API)
GEMINI_LIVE_MODEL=gemini-3.8-live
GEMINI_API_VERSION=v1beta
GEMINI_VOICE_NAME=Puck
```

---

### 3. Execução

#### No Linux / WSL (Ubuntu):

Se estiver utilizando o WSL ou Linux moderno (com proteção PEP 668):

**Opção A: Com Ambiente Virtual (Recomendado):**
```bash
sudo apt update && sudo apt install -y python3-venv
python3 -m venv .venv_wsl
source .venv_wsl/bin/activate
pip install -r requirements.txt
uvicorn src.web.server:app --port 8000 --reload
```

**Opção B: Instalação Direta:**
```bash
python3 -m pip install --break-system-packages -r requirements.txt
python3 -m uvicorn src.web.server:app --port 8000 --reload
```

#### No Windows (PowerShell ou CMD):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.web.server:app --port 8000 --reload
```

---

### 4. Acessando a Aplicação
Abra o navegador no endereço:
👉 **`http://localhost:8000`**

1. Clique em **`▶ START`** para iniciar a prática.
2. Permita o acesso ao microfone pelo navegador.
3. Converse naturalmente em inglês!

Para verificar o status e diagnóstico da API em tempo real:
👉 **`http://localhost:8000/api/health`**

---

## 🧪 Execução de Testes Automatizados

A suíte de testes cobre o armazenamento local, parsing de saídas estruturadas e consistência dos prompts:

```bash
pytest tests/ -v
```

---

## 🗺️ Roadmap de Evolução

- [x] **Fase 1 (Concluída):** Agente de conversação via terminal (texto) com persistência SQLite e categorização de erros.
- [x] **Fase 2 (Concluída):** Conversação falada em tempo real com Gemini Live API, streaming PCM bidirecional e interface Sci-Fi.
- [x] **Fase 2.1 (Concluída):** Estabilização de áudio sem sobreposição de pacotes e regras pedagógicas de acompanhamento de assunto (*thread continuity*).
- [x] **Fase 3.1 (Concluída):** Conectividade em rede local (WSL2 portproxy + firewall) e validação da interface web e WebSocket em smartphone Android real.
- [ ] **Fase 3.2 (Prioritária / Em Investigação):** Resolução da captura de microfone no Android via Contexto Seguro (HTTPS / TLS) para validação da conversa speech-to-speech completa no celular.
- [ ] **Fase 4 (Planejada):** Análise e métricas avançadas de pronúncia e relatórios de progresso do aluno.
- [ ] **Fase 5 (Planejada):** Suporte multiplataforma (aplicativo mobile nativo para Android).

---

## 📄 Licença e Créditos

Este projeto é desenvolvido com foco no ensino e capacitação tecnológica contínua.

**Propriedade e Desenvolvimento:**  
**MHMF Technologies**  
*Transformando o aprendizado de idiomas através da Inteligência Artificial em tempo real.*

**Licença:**  
Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.
