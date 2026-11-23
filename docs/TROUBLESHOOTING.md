# Troubleshooting

Registro dos principais problemas encontrados durante o desenvolvimento do English Speaking Coach.

---

# Git não responde no Windows

## Sintoma

Comandos como:

```powershell
git --version
git status
```

não retornam nada.

## Causa

Instalação corrompida do Git no Windows.

Foi identificado conflito entre:

```text
C:\PortableGit
```

e

```text
C:\Program Files\Git
```

Além de erros de DLL:

```text
Bad Image
liblz1.dll
zlib1.dll
```

## Solução

Utilizar Git pelo WSL.

Exemplo:

```bash
git status
git add .
git commit -m "mensagem"
git push
```

---

# Uvicorn não encontra módulo src

## Sintoma

```text
ModuleNotFoundError: No module named 'src'
```

## Diagnóstico

Verificar estrutura:

```bash
find src -type f
```

Confirmar existência:

```text
src/__init__.py
src/web/__init__.py
src/web/server.py
```

## Solução

Rodar utilizando o ambiente Python correto.

---

# Uvicorn não instalado

## Sintoma

```text
No module named uvicorn
```

## Causa

Execução usando:

```text
/usr/bin/python3
```

sem ambiente virtual.

## Solução

Ativar ambiente:

```bash
source ~/venv-coach/bin/activate
```

Instalar dependências:

```bash
pip install -r requirements.txt
```

---

# Áudio do Coach muito rápido

## Sintoma

A voz parece acelerada.

## Observação

Nem sempre o problema é velocidade.

Em alguns testes o efeito de "fala rápida" foi causado por:

- corte de áudio
- interrupções
- respostas muito longas

## Próximas verificações

- testar outras vozes
- reduzir tamanho das respostas
- usar respostas de 1 a 3 frases
- investigar interrupções na reprodução

---

# Áudio cortado durante resposta

## Sintoma

O texto é gerado completo.

O áudio para no meio da frase.

Exemplo:

```text
Of course! I was saying...
```

e a fala é interrompida.

## Hipóteses

### Barge-In

O sistema detecta nova fala do usuário e interrompe a resposta.

### Reprodução

Problemas de buffer no frontend.

### Streaming

Problemas na reprodução dos chunks de áudio recebidos.

## Diagnóstico

Verificar:

```text
src/web/static/index.html
```

principalmente:

- AudioContext
- MediaRecorder
- WebSocket
- reprodução dos chunks

---

# Conectividade

## Teste realizado

```powershell
ping google.com -n 50
```

Resultado:

```text
0% packet loss
11 ms média
```

## Conclusão

A conexão de internet não aparenta ser a causa principal dos cortes de áudio.

---

# Conectividade de Rede Local entre WSL2, Windows e Dispositivos Externos (LAN)

## Sintoma

Ao tentar acessar a aplicação a partir de um dispositivo móvel (Android) ou outro computador na mesma rede Wi-Fi via `http://<IP-DO-WINDOWS>:8000`, a conexão expira com o erro:

```text
ERR_CONNECTION_TIMED_OUT ou "Não foi possível conectar ao servidor"
```

## Causa Arquitetural

1. O WSL2 opera em uma máquina virtual Hyper-V interna com arquitetura de rede em NAT (sub-rede virtual separada, ex: `172.x.x.x`).
2. O IP do WSL2 não é roteável diretamente a partir da rede local física (`192.168.x.x`).
3. Por padrão, o Windows Defender Firewall bloqueia conexões de entrada de outras máquinas para portas não registradas.

## Solução Implementada

### 1. Obter o IP interno do WSL2
No terminal do WSL2:
```bash
hostname -I
```

### 2. Configurar o Port Forwarding no Windows (Portproxy)
No PowerShell do Windows (executado como Administrador):
```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<IP_DO_WSL2>
```

### 3. Liberar a Porta no Windows Defender Firewall
No PowerShell como Administrador:
```powershell
New-NetFirewallRule -DisplayName "WSL2 Coach 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### 4. Executar o Uvicorn em todas as interfaces
No WSL2:
```bash
python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8000
```

### 5. Verificar status do encaminhamento
```powershell
netsh interface portproxy show v4tov4
```

## Resultado

Acesso externo validado com sucesso. Dispositivos da rede local (smartphones, tablets, outros computadores) conseguem carregar a interface web e conectar ao WebSocket através de `http://<IP-DO-WINDOWS>:8000`.

---

# PROBLEMA EM INVESTIGAÇÃO (Bloqueador Atual): Captura de Microfone no Android

## Status
🔴 **BLOQUEADOR ABERTO** (Fase Mobile / Multi-dispositivo)

## Sintomas Observados

1. O dispositivo móvel (smartphone Android real) acessa o sistema via Wi-Fi pelo IP local (`http://192.168.x.x:8000`).
2. O frontend carrega e renderiza perfeitamente com a interface Sci-Fi completa.
3. O backend FastAPI (WSL2) responde normalmente e estabelece a conexão WebSocket (`/ws`).
4. Sessões e mensagens são criadas e persistidas no SQLite local.
5. A Gemini Live API confirma inicialização da sessão de voz (`session_ready`).
6. **No entanto, a captura de áudio do microfone não funciona.**
7. Ao clicar no botão `▶ START`, a execução é abortada no navegador do celular com a mensagem de erro:

```text
Cannot read properties of undefined (reading 'getUserMedia')
```

## Evidências Encontradas

- O erro é disparado em `src/web/static/index.html` na função `startMicrophone()`:
  ```javascript
  micStream = await navigator.mediaDevices.getUserMedia({ audio: { ... } });
  ```
- Ao inspecionar o console do navegador mobile no Android, constata-se:
  ```javascript
  window.isSecureContext === false
  navigator.mediaDevices === undefined
  ```
- Enquanto no desktop via `http://localhost:8000` o objeto `navigator.mediaDevices` existe e opera normalmente, no dispositivo móvel acessando por IP em HTTP (`http://192.168.x.x:8000`) o objeto é estritamente `undefined`.

## Testes Executados

| Teste | Ambiente | Procedimento | Resultado |
|---|---|---|---|
| **Renderização Web** | Android (Chrome/Firefox) | Acesso a `http://192.168.x.x:8000` | ✅ Sucesso (layout renderizado perfeitamente) |
| **Conexão WebSocket** | Android ↔ WSL2 | Handshake e mensagens de controle `/ws` | ✅ Sucesso (`connected`, `session_ready`) |
| **Persistência SQLite** | Android ↔ Backend | Criação de registro em `sessions` | ✅ Sucesso (sessão registrada com ID) |
| **Gemini Live API** | Backend ↔ Google | Handshake e conexão da Live API | ✅ Sucesso (pronto para receber áudio) |
| **Chamada `getUserMedia`** | Android (Chrome) | Clique em `▶ START` | ❌ **Falha:** `navigator.mediaDevices` é `undefined` |

## Resultados Positivos Consolidados

- ✅ O sistema já é acessível a partir de dispositivos móveis na rede local.
- ✅ O frontend carrega corretamente no Android.
- ✅ O backend responde adequadamente em ambiente WSL2.
- ✅ A conexão WebSocket é estabelecida de forma estável.
- ✅ Sessões e turnos são criados e registrados normalmente no SQLite.
- ✅ A integração com a Gemini Live API está 100% operacional.

## Hipóteses Técnicas Levantadas

1. **Restrição Mandatória de Contexto Seguro (*Secure Context* - W3C Specification):**
   - A especificação da W3C e as políticas de segurança dos motores de navegadores modernos (Chromium / Blink e WebKit) determinam que APIs de captura de hardware sensíveis (`navigator.mediaDevices`, `getUserMedia`, Web Bluetooth, Web Crypto, etc.) **só são expostas em Contextos Seguros**.
   - Por definição técnica, apenas origens servidas por **`https://`** ou **`http://localhost`** (`127.0.0.1`) são consideradas seguras.
   - Conexões via endereço IP de rede local em HTTP inseguro (`http://192.168.x.x:8000`) são classificadas como contexto inseguro. Nesses cenários, o navegador intencionalmente define `navigator.mediaDevices` como `undefined`, impossibilitando a captura de áudio antes mesmo de solicitar qualquer permissão ao usuário.

2. **Permissões do Sistema Operacional Android:**
   - O Android requer permissão explícita de microfone para o aplicativo do navegador, mas o diálogo do sistema nem chega a ser acionado devido ao bloqueio prévio do contexto inseguro no motor web.

3. **Tratamento Defensivo no Frontend:**
   - O código do frontend atual assume a existência incondicional de `navigator.mediaDevices`, sem validação prévia de `window.isSecureContext`, o que causa uma exceção não tratada (*uncaught TypeError*).

## Próximos Passos de Investigação e Resolução

1. **Implementar Terminação TLS/HTTPS Local (Solução Definitiva):**
   - Gerar certificados TLS válidos para desenvolvimento com a ferramenta `mkcert` (para `localhost` e o IP local `192.168.x.x`).
   - Configurar o Uvicorn com suporte nativo a SSL/TLS:
     ```bash
     uvicorn src.web.server:app --host 0.0.0.0 --port 8000 --ssl-keyfile cert-key.pem --ssl-certfile cert.pem
     ```
   - O acesso via `https://192.168.x.x:8000` reativará o `navigator.mediaDevices` no Android.

2. **Utilizar Túnel HTTPS Seguro para Testes Rápidos:**
   - Utilizar utilitários como `Cloudflare Tunnels` (`cloudflared`) ou `ngrok` para expor a porta 8000 sob um domínio HTTPS público e seguro (ex: `https://meu-coach.trycloudflare.com`).
   - Isso garante imediatamente um *Secure Context* oficial no navegador móvel.

3. **Habilitar Flag de Desenvolvimento Temporária no Chrome do Android:**
   - No Chrome do dispositivo Android, acessar: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`.
   - Adicionar a URL da máquina (`http://192.168.x.x:8000`), marcar como `Enabled` e reiniciar o navegador para liberar o microfone em ambiente de desenvolvimento.

4. **Blindar o Frontend (`src/web/static/index.html`):**
   - Inserir checagem defensiva de `window.isSecureContext` e suporte a `navigator.mediaDevices`, exibindo alertas explicativos amigáveis ao usuário caso a página não esteja sendo servida em HTTPS.

---

# Comandos úteis

## Rodar servidor web

```bash
source ~/venv-coach/bin/activate

cd /mnt/f/agent

python -m uvicorn src.web.server:app --host 0.0.0.0 --port 8000
```

## Abrir interface

```text
http://localhost:8000
```

## Verificar Git

```bash
git status
```

## Enviar alterações

```bash
git add .
git commit -m "mensagem"
git push
```

---

# Próxima investigação

Arquivo prioritário:

```text
src/web/static/index.html
```

Objetivo:

Descobrir se o áudio está sendo interrompido pelo microfone, por WebSocket ou pela reprodução dos chunks do Gemini Live.