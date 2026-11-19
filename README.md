# English Speaking Coach

**Um coach de conversação em inglês por voz, criado por um brasileiro para brasileiros.**

O English Speaking Coach é um agente de IA que conversa em inglês, **falando e ouvindo em tempo real**, para que o aluno perca a vergonha de falar. Ele não ensina regras: ele cria o ambiente seguro e constante de que o aluno precisa para praticar, corrige com discrição e acompanha a evolução ao longo do tempo.

> **Status:** a base por texto (Fase 1) está concluída e em validação. O núcleo do produto, a conversa por voz (speech-to-speech), está em desenvolvimento. Veja o [Roadmap](#roadmap).

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
- [Custo e plano gratuito](#custo-e-plano-gratuito)
- [Privacidade e segurança](#privacidade-e-segurança)
- [Visão para Android](#visão-para-android)
- [Roadmap](#roadmap)
- [Como contribuir](#como-contribuir)
- [Aviso](#aviso)

---

## O problema

Para o brasileiro, o maior obstáculo no aprendizado de inglês não é a falta de conteúdo, mas a falta de **prática de fala segura e frequente**. É comum que o estudante:

- tenha medo de errar e de se expor diante de outra pessoa;
- não tenha com quem praticar no dia a dia;
- fique preso à teoria e a exercícios repetitivos;
- consiga ler e entender inglês, mas trave na hora de falar.

## A proposta

Substituir o ciclo "estudar regra → fazer exercício" por um ciclo **"falar → receber um ajuste → continuar falando"**.

O aluno conversa em voz alta com um interlocutor paciente, que não julga, está disponível a qualquer hora e nunca se cansa. O foco é a **fluência e a confiança**. A precisão gramatical vem como consequência da prática constante, não como pré-requisito dela.

## Diferenciais

**Voz como centro da experiência.** O produto é construído em torno da conversa falada em tempo real, o formato que mais se aproxima de uma situação real e o que mais ajuda a vencer a vergonha de falar.

**Conversa primeiro, correção depois.** Cerca de 80% da interação é conversa natural; cerca de 20% é correção. O aluno passa mais tempo falando e menos tempo estudando regras.

**Um erro por vez.** A cada turno, o coach escolhe o ajuste mais relevante e o apresenta de forma gentil, sem sobrecarregar o aluno nem quebrar o ritmo do diálogo.

**Imersão total em inglês.** O coach responde sempre em inglês, mesmo quando o aluno fala em português, incentivando-o a tentar se expressar na língua-alvo.

**Pensado para o aprendiz brasileiro.** O projeto é orientado aos desafios típicos de quem aprende inglês partindo do português: traduções literais, falsos cognatos e a insegurança de falar. A evolução planejada inclui um catálogo próprio desses padrões (veja o [Roadmap](#roadmap)).

**Memória de erros.** Os erros detectados são registrados e categorizados, o que permite identificar reincidências e mostrar quais categorias aparecem com mais frequência. A prática passa a ser uma evolução mensurável.

**Acessível e gratuito para começar.** A arquitetura foi desenhada para funcionar no plano gratuito da API, sem exigir cartão de crédito (veja [Custo e plano gratuito](#custo-e-plano-gratuito)).

**Arquitetura preparada para crescer.** A lógica pedagógica e a base de dados são independentes da interface. O mesmo núcleo atende o terminal, a web e, futuramente, o Android.

## Como o coach se comporta

| Princípio | Comportamento |
|---|---|
| Proporção | ~80% conversa / ~20% correção gentil |
| Foco | 1 erro corrigido por turno |
| Idioma | 100% em inglês, mesmo se o aluno falar em português |
| Tom | Acolhedor, encorajador, sem julgamento |
| Objetivo | Manter o aluno falando |
| Registro | Erros salvos para acompanhamento e detecção de reincidência |

## Estado atual

### Fase 1: Base por texto ✅ (em validação)

| Componente | Descrição | Status |
|---|---|---|
| Configuração | Variáveis centralizadas e validação da chave de API na inicialização | ✅ |
| Agente e prompts | Persona do coach, regras pedagógicas e saída estruturada (`reply` + `error_detected`) | ✅ |
| Integração com o modelo | Chamada ao Gemini com tratamento de limite de requisições, falhas de servidor e timeouts | ✅ |
| Persistência | SQLite com sessões, mensagens e erros | ✅ |
| Análise de erros | Último erro e ranking de categorias mais frequentes | ✅ |
| Interface CLI | Conversa por texto com `/help`, `/errors` e `/exit` | ✅ |
| Testes automatizados | Suíte para armazenamento e agente, com banco em memória | ✅ |
| Versionamento | Código versionado no GitHub | ✅ |
| Validação com uso real | Testes de conversa e ajuste fino de prompts | 🔄 |

### Fase 2: Núcleo de voz 🔄 (em desenvolvimento)

| Componente | Descrição | Status |
|---|---|---|
| Verificação da conexão de voz | Script `scripts/check_live.py` valida chave, modelo e acesso à Live API | 🔄 |
| Conversa por voz no terminal | Microfone → modelo de voz → alto-falante, em tempo real | 🔜 |

### Comandos da CLI (texto)

| Comando | Função |
|---|---|
| `/help` | Exibe os comandos disponíveis |
| `/errors` | Mostra os erros da sessão e o ranking histórico de categorias |
| `/exit` ou `/quit` | Encerra a sessão com segurança |

## Arquitetura

```text
Aluno (voz)
   │
   ▼
Cliente de áudio ── hoje: terminal · depois: web · depois: Android
   │   áudio PCM 16 kHz
   ▼
Camada de voz (Gemini Live API, áudio para áudio)
   │   instruções do coach + resposta falada em inglês
   │   transcrição da fala do aluno e do coach
   ▼
Coach Agent  ──►  Prompts (regras pedagógicas)
   │
   ▼
Análise de erros (assíncrona, sobre a transcrição)
   │
   ▼
SQLite (sessões, mensagens, erros)
```

Pontos de design:

- O modelo de voz conduz a conversa. O coach corrige durante a fala, seguindo as regras pedagógicas definidas nas instruções do sistema.
- A **transcrição** de cada turno alimenta uma análise separada, que detecta e categoriza o erro **sem interromper o diálogo**. É essa análise que alimenta o `/errors` e o histórico.
- O cliente de áudio é uma camada substituível. Trocar o terminal pela web ou pelo Android não altera o restante.

## Estrutura do projeto

```text
.
├── src/
│   ├── main.py              # Interface CLI e loop de conversa por texto
│   ├── config.py            # Configurações e validação do ambiente
│   ├── agent/
│   │   ├── coach.py         # Lógica do agente e integração com o modelo
│   │   └── prompts.py       # Persona e regras pedagógicas
│   └── storage/
│       ├── database.py      # Criação e conexão do banco SQLite
│       └── repository.py    # Sessões, mensagens, erros e consultas
├── scripts/
│   └── check_live.py        # Verifica a conexão com a Live API (voz)
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
| **Gemini Live API** (`gemini-3.8-live`) | Conversa por voz em tempo real (áudio para áudio) |
| **Gemini API (texto)** (`gemini-3.6-flash`) | Análise de erros, modo texto e testes |
| **google-genai** | Biblioteca oficial para acessar a API |
| **SQLite** | Banco de dados local para histórico e erros |
| **pip e `requirements.txt`** | Gerenciamento de dependências |
| **python-dotenv / `.env`** | Configuração e proteção de credenciais |
| **Pytest** | Testes automatizados |
| **Git e GitHub** | Controle de versão e hospedagem do código |
| **WSL** | Ambiente Linux no Windows para o fluxo de versionamento |

Tecnologias planejadas: captura e reprodução de áudio no terminal (`sounddevice`), servidor web com WebSocket (FastAPI), cliente web instalável (PWA) e empacotamento para Android.

## Como executar

### Pré-requisitos

- Python 3
- Chave de API do Google AI Studio (conta gratuita, **sem faturamento vinculado**)
- Microfone e fones de ouvido (recomendado, para evitar eco na conversa por voz)

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
GEMINI_MODEL=gemini-3.6-flash
GEMINI_LIVE_MODEL=gemini-3.8-live
```

> Nunca versione o arquivo `.env`. Ele já está listado no `.gitignore`.

> Os modelos do Gemini mudam com frequência. Se algum deles for descontinuado, consulte a lista oficial em `ai.google.dev/gemini-api/docs/models` e ajuste os nomes acima.

### 5. Verifique a conexão de voz

```bash
python scripts/check_live.py
```

Se tudo estiver certo, o script mostra uma frase de resposta do modelo de voz. Em caso de erro, ele indica o provável motivo (chave, modelo ou limite).

### 6. Execute o coach por texto

```bash
python src/main.py
```

ou

```bash
python -m src.main
```

> Para a conversa por voz, execute o projeto com o Python do **Windows** (PowerShell), e não pelo WSL, que costuma ter dificuldade para acessar microfone e som.

## Testes

```bash
python -m pytest tests/
```

Os testes usam um banco SQLite em memória (`:memory:`) e, portanto, não alteram o banco real nem consomem a cota da API.

## Custo e plano gratuito

O projeto foi pensado para rodar **sem custo** no plano gratuito do Google AI Studio:

- Os modelos de voz e de texto utilizados têm camada gratuita, com limites de uso que podem mudar. Consulte os limites atuais do seu projeto no Google AI Studio.
- Para garantir que não haja cobrança, **não vincule uma conta de faturamento** ao projeto da chave de API.
- No plano gratuito, sessões de voz têm duração limitada. O cliente deve tratar o encerramento e a retomada da sessão.
- Ao ultrapassar a cota gratuita, a API retorna erro de limite (429). O coach trata esse caso e informa o aluno em vez de falhar.

## Privacidade e segurança

- Histórico de sessões, mensagens e erros ficam armazenados **localmente**, em SQLite.
- A chave da API fica no `.env`, que não é enviado ao repositório.
- **Atenção:** o áudio e a transcrição das conversas são enviados à API do Gemini para gerar as respostas. No plano gratuito, os termos do Google indicam que esse conteúdo pode ser usado para melhorar os produtos da empresa. No plano pago, não. Evite compartilhar informações pessoais ou sensíveis durante a prática.
- Em versões para Android e web, a chave da API **nunca** será embutida no aplicativo. O acesso será feito por um servidor intermediário ou por tokens temporários.

## Visão para Android

O objetivo é levar o coach para o celular, onde a prática por voz é mais natural. O caminho planejado, do mais simples ao mais completo:

1. **Cliente web com microfone**, acessado pelo navegador do Android e instalável na tela inicial (PWA). Não exige loja de aplicativos e é gratuito.
2. **Empacotamento como aplicativo Android** a partir do mesmo cliente web, para distribuir um APK. A publicação na Play Store é opcional e envolve taxa de desenvolvedor.
3. **Aplicativo Android nativo**, se a experiência exigir recursos específicos do aparelho.

Para isso, o núcleo (agente, prompts, banco de dados e análise de erros) é mantido separado da interface, e a comunicação com o modelo de voz passará por um servidor intermediário, que protege a chave da API.

## Roadmap

### Fase 1: Base por texto ✅
- [x] Conversa em inglês via terminal
- [x] Persistência local (SQLite)
- [x] Registro e categorização de erros
- [x] Testes automatizados
- [ ] Validação com uso real e ajuste fino de prompts

### Fase 2: Núcleo de voz (speech-to-speech) 🔄
- [ ] Verificação da conexão com a Live API (`scripts/check_live.py`)
- [ ] Conversa por voz no terminal (microfone → modelo → alto-falante)
- [ ] Instruções do coach adaptadas à voz (80/20, um erro por vez, só inglês)
- [ ] Transcrição de cada turno salva no banco de dados
- [ ] Análise assíncrona de erros sobre a transcrição
- [ ] Tratamento de limites do plano gratuito e de sessões longas

### Fase 3: Cliente web 🔜
- [ ] Servidor intermediário (FastAPI + WebSocket) que protege a chave da API
- [ ] Página web com captura de microfone e reprodução da resposta em tempo real
- [ ] Reaproveitamento integral do agente e do banco de dados
- [ ] Funcionamento no navegador do Android

### Fase 4: Android 🔜
- [ ] Instalação como PWA na tela inicial
- [ ] Empacotamento em aplicativo Android (APK)
- [ ] Ajustes de uso em celular: fones, bloqueio de tela e economia de bateria

### Fase 5: Personalização e evolução do aluno 💡
- [ ] Níveis de conversação (do iniciante ao avançado, alinhados ao CEFR)
- [ ] Cenários práticos: entrevista de emprego, viagem, reuniões, atendimento ao cliente
- [ ] Catálogo de erros típicos de brasileiros (falsos cognatos, tradução literal, preposições)
- [ ] Revisão periódica dos erros recorrentes, retomados no contexto de uma conversa
- [ ] Painel de métricas: tempo de fala, erros por categoria, evolução semanal
- [ ] Perfil do aluno: objetivos, interesses e tópicos preferidos

### Fase 6: Pronúncia 💡
- [ ] Feedback de pronúncia
- [ ] Simulação de situações reais com voz contínua

**Legenda:** ✅ concluído · 🔄 em andamento · 🔜 próximo · 💡 planejado

## Como contribuir

Sugestões, ideias e feedbacks são bem-vindos. Abra uma *issue* descrevendo o problema ou a proposta. Para contribuições de código, abra um *pull request* explicando a mudança e, quando possível, incluindo testes.

## Aviso

Este é um projeto experimental, parte de um processo de pesquisa e validação sobre como agentes de IA podem atuar como coaches de conversação para estudantes brasileiros de inglês.

O objetivo principal não é ensinar gramática, mas ajudar pessoas a desenvolver **confiança para se comunicar em inglês** através da prática constante.
