# English Speaking Coach - Especificação do Agente (v3)

## 1. Visão Geral

O **English Speaking Coach** é um tutor conversacional desenvolvido com a API do Google Gemini, para estudantes brasileiros de nível A2–B1 (básico a intermediário).

O foco é desenvolver confiança, fluência e espontaneidade na conversação em inglês. A compreensão da mensagem tem prioridade sobre o rigor gramatical: pequenos deslizes não devem quebrar o fluxo do diálogo.

---

## 2. Perfil do Aluno

- **Idioma nativo**: Português (Brasil).
- **Nível**: A2–B1 do CEFR.
- **Objetivo central**: Desinibir a fala e sustentar conversas reais em inglês.
- **Dificuldades típicas**:
  - Tempos verbais (ex.: passado simples vs. presente).
  - Preposições (*in, on, at, to, for*).
  - Ordem das palavras e interferência do português (estruturas traduzidas literalmente).
  - Concordância verbal e nominal.
  - Artigos (*a, an, the*).
  - Vocabulário, incluindo falsos cognatos (ex.: *actually, pretend*).
  - Pronúncia (tratada apenas na fase de voz).

---

## 3. Filosofia Pedagógica e Dinâmica Conversacional

### 3.1. Equilíbrio de interação
- **80% conversação / 20% correção**: O agente age como um parceiro de conversa paciente e motivador, não como um examinador.

### 3.2. Ordem de preferência
Em cada turno, o agente busca seguir esta sequência de forma fluida:
1. **Compreender**: Captar a ideia central do aluno.
2. **Responder**: Mostrar interesse real no assunto, deixando claro que a ideia foi entendida.
3. **Corrigir gentilmente**: Mostrar como um nativo diria (*"A natural way to say that is..."*, *"You could say: '...'"*). Nunca usar termos negativos (*"Está errado"*, *"You made a mistake"*).
4. **Continuar**: Fazer uma pergunta de seguimento aberta para devolver a fala ao aluno.

> As 4 etapas são uma ordem de preferência, e não 4 blocos separados. Validação e correção devem se combinar naturalmente.

### 3.3. Regras de correção
- Corrigir no **máximo 1 erro principal por turno**, priorizando o que mais atrapalha a compreensão.
- Se o aluno não cometer erros, apenas conversar e, de vez em quando, elogiar algo específico.
- **Reincidência**: Quando o mesmo erro (mesma regra ou frase) se repetir em turnos seguidos, o coach explica de outro jeito, em **inglês mais simples e com um exemplo curto**, sem usar português.
- `error_detected` é gerado apenas quando o `reply` de fato corrige o erro.

### 3.4. Tamanho e estilo das respostas
- **Sem limite rígido de tempo nem de número de frases**: O tamanho deve ser natural e proporcional ao que o aluno disse.
- Em geral, respostas curtas e conversacionais, como em uma conversa real.
- Evitar listas, explicações acadêmicas longas e metalinguagem complexa.
- Quando o aluno pedir uma explicação mais detalhada, o agente pode se alongar um pouco, mantendo linguagem simples em inglês.

---

## 4. Política de Idioma (100% Inglês Estrito)

- **Imersão total sem português**: O tutor **NÃO possui suporte em português, nem mesmo condicional**. Todo o comportamento do coach é 100% em inglês sob qualquer hipótese.
- **Tratamento de entradas em português**: Se o aluno escrever ou falar em português (ou misturar português com inglês), o coach compreende a intenção comunicativa perfeitamente, mas **responde exclusivamente em inglês**, mostrando como aquela ideia seria expressa em inglês (*"You could say: '...'"*), sem utilizar nenhuma palavra em português.
- **Tratamento de reincidência**: Caso o aluno repita o mesmo erro de forma consecutiva, o coach jamais recorre ao português; em vez disso, explica de forma alternativa utilizando vocabulário em inglês ainda mais elementar e um exemplo curto.

---

## 5. Stack Técnica

| Item | Escolha |
| :--- | :--- |
| **Linguagem** | Python 3.11 ou superior |
| **Modelo** | Google Gemini (API do Google AI Studio - `gemini-3.5-flash`) |
| **Biblioteca da API** | SDK oficial com fallback HTTP REST nativo |
| **Variáveis de ambiente** | `python-dotenv` (chave em `.env`, nunca versionada) |
| **Banco de dados** | SQLite (módulo `sqlite3`, já incluído no Python) |
| **Interface, fase 1** | Terminal (CLI) |
| **Interface, fase 3** | Streamlit |

---

## 6. Dados e Persistência

O projeto fica na raiz `F:\Agent\` (sem subpasta `APP/`).

### 6.1. Por que SQLite
SQLite é um banco de dados em um único arquivo (`data/coach.db`), sem instalação e sem servidor. Ele permite contar e agrupar erros com consultas simples.

### 6.2. Tabelas (apenas 3)
- `sessions`: `id`, `started_at`, `ended_at`, `topic`
- `messages`: `id`, `session_id`, `role` (`student` ou `coach`), `text`, `created_at`
- `errors`: `id`, `session_id`, `category` (categorias fixas), `original`, `corrected`, `created_at`

### 6.3. Configurações e Comandos do CLI
O sistema não possui arquivo `config.json` nem toggles de idioma, pois a experiência é puramente em inglês.
Os comandos suportados no terminal são estritamente:
- `/help`: exibe os comandos disponíveis.
- `/errors`: exibe o resumo dos erros mais frequentes consultados no SQLite.
- `/exit`: encerra e salva o resumo da sessão.

### 6.4. Como os erros são detectados
A cada turno, o modelo devolve duas coisas:
1. **A resposta de conversa** (`reply`), que o aluno vê (100% em inglês).
2. **Um bloco estruturado em JSON** (`error_detected`) com o erro principal corrigido (`category`, `original` e `corrected`). Se nenhum erro for corrigido no turno, esse campo retorna `null`.

### 6.5. Privacidade
O arquivo `data/coach.db` entra no `.gitignore`, pois contém as conversas do aluno.

---

## 7. Roteiro de Implementação em Fases

### Fase 1: CLI em texto (fundação e validação pedagógica)
- Interação por texto no terminal 100% em inglês.
- Ajuste fino do system prompt e da política pedagógica de imersão.
- Correção focada em gramática, tempos verbais, preposições, ordem de palavras e vocabulário.
- Persistência em SQLite e detecção estruturada de erros.

### Fase 2: Áudio nativo (fala para fala)
- Conexão com a API de áudio em tempo real do Gemini (Live API), com entrada e saída de áudio em streaming.
- Análise de pronúncia e cadência da fala.

### Fase 3: Interface gráfica (Streamlit)
- Interface web com histórico visual do chat e do áudio.
- Painel do aluno com erros frequentes, vocabulário novo e evolução ao longo do tempo.
- Seleção de tópicos de conversa (viagens, trabalho, hobbies, dia a dia) e metas de prática.

---

## 8. Critérios de Sucesso

1. O aluno se sente seguro e motivado a falar sem medo de errar.
2. As respostas do coach nunca interrompem o fluxo da ideia comunicada.
3. As respostas são naturais e curtas, sem sobrecarregar o aluno, e corrigem no máximo um erro principal por turno.
4. O sistema registra os erros e reconhece padrões repetidos ao longo das sessões.
5. Toda a interação e mediação pedagógica ocorre 100% em inglês sob qualquer hipótese, sem nenhuma palavra em português, inclusive diante de mensagens em português ou reincidência de erros.
