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

A conexão não aparenta ser a causa principal dos cortes de áudio.

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