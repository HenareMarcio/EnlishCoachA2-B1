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

---

## [2026-11-23] - Otimização de Áudio, Inteligência Conversacional, Refatoração do Backend e UI Sci-Fi

- **1. Resolução do Bug da Voz "Atropelada" no Frontend (`src/web/static/index.html`)**:
  - **Diagnóstico**: Na reprodução do Web Audio API, `nextPlayTime = playbackAudioCtx.currentTime` era executado a cada chunk recebido. Como pacotes de áudio chegavam com milissegundos de intervalo, cada novo bloco iniciava no tempo presente, tocando sobreposto ao anterior e gerando uma cacofonia acelerada e ininteligível.
  - **Correção**: `nextPlayTime` agora é inicializado estritamente na criação do contexto ou quando há silêncio real (`nextPlayTime < now`), aplicando uma margem de segurança de `+0.04s` (40 ms de jitter buffer) e agendando cada bloco subsequente de forma perfeitamente sequencial (`nextPlayTime += audioBuffer.duration`).
  - **Buffer de Envio do Microfone**: Agrupamento de amostras do `AudioWorklet` em blocos estáveis de ~100 ms (1.600 amostras a 16 kHz), eliminando a sobrecarga de disparar centenas de micro-frames WebSocket por segundo.

- **2. Evolução Pedagógica: Parceiro de Conversa vs. Chatbot Genérico (`src/agent/prompts.py`)**:
  - **Manutenção do Fio da Conversa (*Thread Continuity*)**: O Coach foi instruído a abandonar o padrão mecânico de questionador/interrogador. Agora ele escuta, valida o ponto trazido pelo aluno e aprofunda estritamente o mesmo assunto em vez de inventar novos tópicos aleatórios.
  - **Tratamento Especializado do "Mais" Brasileiro**: Reconhecimento de padrões típicos de estudantes brasileiros que dizem *"mais"*, *"again"*, *"repeat"*, *"what?"*, *"sorry?"*, *"como?"* ou *"não entendi"*. O coach compreende o pedido de repetição, reescreve a ideia em inglês mais simples, mantém o assunto e oferece 2 ou 3 opções concretas para ajudar o aluno a responder.
  - **Cadência Conversacional Natural**: Ritmo estabilizado em ~130 WPM com enunciação fluida e correções discretas por reformulação (*recasting*).

- **3. Refatoração Arquitetural e Resiliência do Servidor (`src/web/server.py`)**:
  - **Lifespan Moderno**: Substituído o evento `@app.on_event("startup")` pelo context manager assíncrono `@asynccontextmanager lifespan(app: FastAPI)`.
  - **Supervisão de Concorrência**: Implementada inspeção obrigatória de `task.exception()` para as tarefas de streaming do `asyncio.wait()`, impedindo que erros da Gemini Live API (como 400 ou 429) fiquem silenciados em segundo plano.
  - **VAD Otimizado**: Removido o bloqueio forçado de 1.3s de silêncio morto (`silence_duration_ms=1300`), permitindo respostas rápidas com baixa latência nativa.
  - **Safe Senders para WebSockets**: Criados os auxiliares `safe_send_json` e `safe_send_bytes` com validação de `WebSocketState.CONNECTED`, evitando exceções do Starlette por tentativas de escrita em conexões encerradas.
  - **Seleção de Vozes (`SpeechConfig`)**: Suporte a prebuilt voices (`Puck`, `Aoede`, etc.) configurável via `GEMINI_VOICE_NAME` em `src/config.py`.
  - **Endpoint de Saúde**: Adicionada a rota `GET /api/health` para testes rápidos de status do servidor e API key.

- **4. Nova Interface Visual Sci-Fi (`src/web/static/index.html`)**:
  - Limpeza de tags HTML de editor contaminadas (`<em>`, `<strong>`, `<br>`).
  - Paleta de cores temática espacial escura com efeitos neon ciano (`#00e5ff`) e cartões com *glassmorphism* (efeito de vidro translúcido).
  - Avatar robótico inteligente com animação de flutuação suave (`@keyframes float`).
  - Substituição dos botões duplicados por um botão de controle único `▶ START` / `■ STOP`.
  - Novo indicador visual dinâmico *"Pensando"* (`● ● ●`).
  - Substituição dos rótulos anteriores por designações limpas e diretas: `ME` (aluno) e `COACH`.
  - Rodapé com destaque institucional oficial: **Developed by MHMF Technologies**.

- **5. Documentação Profissional e Versionamento (`README.md` e `.gitignore`)**:
  - Atualização completa do `README.md` com tom corporativo e técnico, diagramas em ASCII do pipeline de áudio, instruções completas para Windows e Linux/WSL (tratando restrições do PEP 668) e roadmap.
  - Adição de regras no `.gitignore` para ignorar arquivos temporários de backup (`*.bak`, `*.backup.*`) e ambientes Linux (`.venv_wsl/`).

---

## [2026-11-23] - Governança Open Source, Conectividade em Rede Local (WSL2/LAN) e Validação Mobile (Android)

- **1. Governança e Publicação da Licença MIT**:
  - Inclusão oficial do arquivo `LICENSE` com a licença MIT padrão de código aberto (Copyright (c) 2026 Marcio Henare).
  - Governança de documentação consolidada e sincronização bem-sucedida do repositório remoto no GitHub (`https://github.com/HenareMarcio/EnlishCoachA2-B1.git`), com envio de todos os commits pendentes na branch `main`.

- **2. Conectividade de Rede Local entre WSL2, Windows Host e Dispositivos Externos**:
  - **Desafio Arquitetural**: O WSL2 opera em uma máquina virtual Hyper-V isolada sob NAT com endereço IP próprio (ex: `172.x.x.x`), impedindo que outros dispositivos da rede Wi-Fi local (como smartphones) alcancem a porta `8000` diretamente pelo IP do Windows (`192.168.x.x`).
  - **Solução Técnica Implementada**:
    1. **Encaminhamento de Portas (*Portproxy*)**: Configuração do `netsh` no Windows para rotear conexões externas para a sub-rede do WSL2:
       ```cmd
       netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<IP_DO_WSL2>
       ```
    2. **Firewall do Windows**: Criação de regra de entrada no Windows Defender Firewall permitindo tráfego TCP na porta 8000.
    3. **Binding no Uvicorn**: Servidor FastAPI configurado para vincular em `0.0.0.0`, permitindo conexões em todas as interfaces de rede física e virtual.
  - **Resultado**: O sistema passou a ser acessado perfeitamente por outros dispositivos conectados na mesma rede local.

- **3. Validação do Acesso Mobile em Dispositivo Android Real**:
  - **Frontend Responsivo**: Interface web Sci-Fi carregada e renderizada com fidelidade visual no navegador de um smartphone Android real.
  - **Backend Operacional**: Backend FastAPI operando de forma estável no ambiente WSL2 atendendo requisições do dispositivo móvel.
  - **WebSocket, SQLite e Live API**: Conexão WebSocket estabelecida com sucesso; sessões e logs gravados corretamente no banco SQLite; integração com a Gemini Live API inicializada normalmente (`session_ready`).

- **4. Bloqueador Atualmente Aberto (Em Investigação - Captura de Microfone no Android)**:
  - **Sintoma Observado**: Ao clicar em `▶ START` no navegador do celular Android, o fluxo é interrompido com o erro de alerta:
    ```text
    "Cannot read properties of undefined (reading 'getUserMedia')"
    ```
  - **Diagnóstico Preliminar**:
    - O objeto `navigator.mediaDevices` é avaliado como `undefined` no navegador mobile (Chromium/Android).
    - A causa raiz primária é a política mandatória de **Contexto Seguro (*Secure Context*)** da W3C: navegadores modernos desabilitam APIs de captura de hardware sensíveis (`getUserMedia`) em origens HTTP não criptografadas que não sejam `localhost`. Como o acesso ocorre via IP de rede local (`http://192.168.x.x:8000`), o navegador bloqueia a API intencionalmente por segurança.
  - **Próximos Passos Prioritários**:
    - Configurar terminação TLS/HTTPS local (via certificados confiáveis com `mkcert` ou túnel HTTPS com `Cloudflare Tunnels` / `ngrok`) ou configurar flags de desenvolvimento temporárias no navegador Android (`chrome://flags/#unsafely-treat-insecure-origin-as-secure`) para validar a conversa speech-to-speech completa no celular.


