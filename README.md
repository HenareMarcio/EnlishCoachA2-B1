# English Speaking Coach

**Um coach de conversação em inglês, criado por um brasileiro para brasileiros.**

O English Speaking Coach é um agente de IA que simula conversas reais em inglês e atua como coach de comunicação. Ele não ensina regras: ele cria o ambiente seguro e constante de que o aluno precisa para **falar**, corrige com discrição e acompanha a evolução ao longo do tempo.

> **Status:** Fase 1 (coach por texto) concluída e em validação. Fases seguintes planejadas no [Roadmap](#roadmap).

---

## Sumário

- [O problema](#o-problema)
- [A proposta](#a-proposta)
- [Diferenciais](#diferenciais)
- [Como o coach se comporta](#como-o-coach-se-comporta)
- [Estado atual](#estado-atual)
- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Tecnologias](#tecnologias)
- [Como executar](#como-executar)
- [Testes](#testes)
- [Privacidade e segurança](#privacidade-e-segurança)
- [Roadmap](#roadmap)
- [Como contribuir](#como-contribuir)
- [Aviso](#aviso)

---

## O problema

Para o brasileiro, um dos maiores obstáculos no aprendizado de inglês não é a falta de conteúdo, mas a falta de **prática de conversação segura e frequente**. É comum que o estudante:

- tenha medo de errar e se expor;
- não tenha com quem praticar no dia a dia;
- fique preso à teoria e a exercícios repetitivos;
- consiga ler e entender inglês, mas trave na hora de falar.

## A proposta

Substituir o ciclo "estudar regra → fazer exercício" por um ciclo **"conversar → receber um ajuste → continuar conversando"**.

O foco do projeto é a **fluência e a confiança**, e a perfeição gramatical vem como consequência da prática constante, não como pré-requisito dela.

## Diferenciais

**Conversa primeiro, correção depois.** Cerca de 80% da interação é conversa natural; apenas cerca de 20% é correção. O aluno passa mais tempo falando e menos tempo estudando regras.

**Um erro por vez.** A cada turno, o coach escolhe o ajuste mais relevante e o apresenta de forma gentil, sem sobrecarregar o aluno nem quebrar o ritmo do diálogo.

**Imersão total em inglês.** O coach responde sempre em inglês, mesmo quando o aluno escreve em português, incentivando-o a tentar se expressar na língua-alvo.

**Pensado para o aprendiz brasileiro.** O projeto é orientado aos desafios típicos de quem aprende inglês partindo do português: traduções literais, falsos cognatos e a insegurança de falar. A evolução planejada inclui um catálogo próprio desses padrões (veja o [Roadmap](#roadmap)).

**Memória de erros.** Cada erro detectado é registrado e categorizado. O sistema identifica reincidências e mostra quais categorias aparecem com mais frequência, transformando a prática em evolução mensurável.

**Seus dados ficam com você.** Histórico e erros são armazenados localmente em SQLite, sem depender de contas ou serviços de terceiros além da API do modelo de linguagem.

**Arquitetura preparada para crescer.** O "cérebro" do coach é independente da interface. Isso permite evoluir do terminal para voz e para web reaproveitando a mesma lógica pedagógica e a mesma base de dados.

## Como o coach se comporta

| Princípio | Comportamento |
|---|---|
| Proporção | ~80% conversa / ~20% correção gentil |
| Foco | 1 erro corrigido por turno |
| Idioma | 100% em inglês, mesmo se o aluno escrever em português |
| Tom | Acolhedor, encorajador, sem julgamento |
| Objetivo | Manter o aluno falando |
| Registro | Erros salvos para acompanhamento e detecção de reincidência |

## Estado atual

### Fase 1: Coach por texto (MVP)

| Componente | Descrição | Status |
|---|---|---|
| Configuração | Variáveis centralizadas e validação da chave de API na inicialização | ✅ |
| Agente e prompts | Persona do coach, regras pedagógicas e saída estruturada (`reply` + `error_detected`) | ✅ |
| Integração com o modelo | Chamada ao Gemini com tratamento de limite de requisições, falhas de servidor e timeouts, com novas tentativas | ✅ |
| Persistência | SQLite com sessões, mensagens e erros | ✅ |
| Análise de erros | Último erro e ranking de categorias mais frequentes | ✅ |
| Interface CLI | Conversa no terminal com os comandos `/help`, `/errors` e `/exit` | ✅ |
| Testes automatizados | Suíte para armazenamento e agente, com banco em memória | ✅ |
| Versionamento | Código versionado no GitHub | ✅ |
| Validação com uso real | Testes de conversa e ajuste fino de prompts | 🔄 Em andamento |

### Comandos da CLI

| Comando | Função |
|---|---|
| `/help` | Exibe os comandos disponíveis |
| `/errors` | Mostra os erros da sessão atual e o ranking histórico de categorias |
| `/exit` ou `/quit` | Encerra a sessão com segurança |

O encerramento por `Ctrl+C` também é tratado: a sessão é finalizada e registrada normalmente no banco de dados.

## Arquitetura

```text
Aluno
  │
  ▼
Interface (hoje: CLI · futuro: voz e web)
  │
  ▼
Coach Agent  ──►  Prompts (regras pedagógicas)
  │
  ▼
Gemini API
  │
  ▼
Resposta em inglês + erro detectado (saída estruturada)
  │
  ▼
SQLite (sessões, mensagens, erros)
```

A interface é uma camada substituível. O Coach Agent e a camada de dados permanecem os mesmos quando o projeto evolui para voz e web.

## Estrutura do projeto

```text
.
├── src/
│   ├── main.py              # Interface CLI e loop de conversa
│   ├── config.py            # Configurações e validação do ambiente
│   ├── agent/
│   │   ├── coach.py         # Lógica do agente e integração com o modelo
│   │   └── prompts.py       # Persona e regras pedagógicas
│   └── storage/
│       ├── database.py      # Criação e conexão do banco SQLite
│       └── repository.py    # Sessões, mensagens, erros e consultas
├── tests/
│   ├── test_storage.py      # Testes da camada de dados
│   └── test_agent.py        # Testes do agente
├── requirements.txt         # Dependências
├── .env                     # Configurações locais (não versionado)
└── .gitignore
```

## Tecnologias

| Tecnologia | Função no projeto |
|---|---|
| **Python** | Linguagem principal |
| **Gemini API** | Modelo de linguagem que gera as respostas do coach |
| **SQLite** | Banco de dados local para histórico e erros |
| **pip e `requirements.txt`** | Gerenciamento de dependências |
| **python-dotenv / `.env`** | Configuração e proteção de credenciais |
| **Pytest** | Testes automatizados |
| **Git e GitHub** | Controle de versão e hospedagem do código |
| **WSL** | Ambiente Linux no Windows para o fluxo de versionamento |

Tecnologias planejadas: Speech-to-Text (STT), Text-to-Speech (TTS), Streamlit e Live API.

## Como executar

### Pré-requisitos

- Python 3
- Chave de API do Google AI Studio (Gemini)

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
cd SEU-REPOSITORIO
```

### 2. Crie e ative um ambiente virtual (recomendado)

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Linux / macOS / WSL:

```bash
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=SUA_CHAVE
GEMINI_MODEL=gemini-3.5-flash
```

> Nunca versione o arquivo `.env`. Ele já está listado no `.gitignore`.

### 5. Execute

```bash
python src/main.py
```

ou

```bash
python -m src.main
```

Se a chave de API estiver ausente ou inválida, o programa exibe orientações claras e encerra sem mostrar erros técnicos.

## Testes

```bash
python -m pytest tests/
```

Os testes usam um banco SQLite em memória (`:memory:`) e, portanto, não alteram o banco real nem consomem a cota da API.

## Privacidade e segurança

- Histórico e erros ficam armazenados **localmente**.
- A chave da API fica no `.env`, que não é enviado ao repositório.
- As mensagens do aluno são enviadas à Gemini API apenas para gerar a resposta do coach.

## Roadmap

### Fase 1: Coach por texto ✅
- [x] Conversa em inglês via terminal
- [x] Persistência local (SQLite)
- [x] Registro e categorização de erros
- [x] Testes automatizados
- [ ] Validação com uso real e ajuste fino de prompts

### Fase 2: Conversação por voz 🔜
- [ ] Speech-to-Text: o aluno fala e a fala é transcrita
- [ ] Text-to-Speech: o coach responde em áudio
- [ ] Ciclo completo de conversa falada (voz → texto → coach → texto → voz)
- [ ] Validação do ciclo primeiro no terminal, antes da interface gráfica

### Fase 3: Interface web 🔜
- [ ] Interface web simples (ex.: Streamlit) com gravação de áudio e player
- [ ] Reaproveitamento integral do Coach Agent e do banco de dados
- [ ] Experiência de uso mais acessível para quem não usa terminal

### Fase 4: Personalização e evolução do aluno 💡
- [ ] Níveis de conversação (do iniciante ao avançado, alinhados ao CEFR)
- [ ] Cenários práticos: entrevista de emprego, viagem, reuniões, atendimento ao cliente
- [ ] Catálogo de erros típicos de brasileiros (falsos cognatos, tradução literal, preposições)
- [ ] Revisão periódica dos erros recorrentes, com retomada no contexto de uma conversa
- [ ] Painel de métricas: tempo de fala, erros por categoria, evolução semanal
- [ ] Perfil do aluno: objetivos, interesses e tópicos preferidos

### Fase 5: Tempo real e pronúncia 💡
- [ ] Conversação fluida em tempo real com Live API
- [ ] Feedback de pronúncia
- [ ] Modo de simulação de situações reais com voz contínua

**Legenda:** ✅ concluído · 🔜 próximo · 💡 planejado

## Como contribuir

Sugestões, ideias e feedbacks são bem-vindos. Abra uma *issue* descrevendo o problema ou a proposta. Para contribuições de código, abra um *pull request* explicando a mudança e, quando possível, incluindo testes.

## Aviso

Este é um projeto experimental, parte de um processo de pesquisa e validação sobre como agentes de IA podem atuar como coaches de conversação para estudantes brasileiros de inglês.

O objetivo principal não é ensinar gramática, mas ajudar pessoas a desenvolver **confiança para se comunicar em inglês** através da prática constante.
