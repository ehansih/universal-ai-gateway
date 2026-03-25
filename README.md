# Universal AI Gateway

A unified gateway that connects to all major AI agents — Claude, ChatGPT, Gemini, and local models via Ollama — and lets them collaborate using the **MACP (Multi-Agent Collaboration Protocol)** to produce the best possible answer.

---

## What it does

Instead of asking multiple AIs separately and combining answers yourself:

```
Without Gateway:
User → ChatGPT  → Answer A
User → Claude   → Answer B
User → Gemini   → Answer C
User manually combines...

With Gateway:
User → Universal AI Gateway → Best Answer
```

---

## Features

- **Auto Mode** — detects your task type (code, math, creative, search) and routes to the best AI
- **Collaborate Mode** — multiple AIs debate using MACP protocol and return one unified best answer
- **Ask All Mode** — sends your question to all available AIs and shows all responses side by side
- **Single Agent Mode** — talk to a specific AI (Claude / ChatGPT / Gemini / Ollama)
- **Plug-in Architecture** — add any new AI agent by creating one file
- **Web UI** — clean dark-themed chat interface in your browser
- **Fallback** — if one AI fails, automatically falls back to the next available one

---

## Supported AI Agents

| Agent | Model | Requires |
|-------|-------|---------|
| Claude | claude-sonnet-4-6 | Anthropic API key |
| ChatGPT | gpt-4o | OpenAI API key |
| Gemini | gemini-1.5-pro | Google API key |
| Ollama | llama3 (or any) | Local Ollama install (free) |

---

## MACP — Multi-Agent Collaboration Protocol

MACP is a 3-round debate protocol between AI agents:

```
ROUND 1 — Claude answers independently
ROUND 2 — ChatGPT critiques and enhances Claude's answer
ROUND 3 — Claude synthesizes both into the final best answer
```

Message encoding uses **AXON-1** format:
```
[CMD] > [SUBJECT] : [PREDICATE] ~ [CONTEXT] | [CONFIDENCE]

Example:
@QRY >> AGENT_2 : BEST_ROUTE ~ LOC:DELHI>MUMBAI | TIME:NOW !!
@RSP : ROUTE~~NH48 | DURATION:14H | CONF:0.87
```

Full MACP specification: [macp-protocol repo](https://github.com/ehansih/macp-protocol)

---

## Smart Routing

The gateway automatically detects the task type and picks the best AI:

| Task Type | Best Agent | Keywords |
|-----------|-----------|---------|
| Code | Claude | code, script, bug, function |
| Math | ChatGPT | calculate, equation, solve |
| Creative | Claude | write, poem, story, essay |
| Search | Gemini | latest, news, today, recent |
| Reasoning | Claude | why, explain, compare, analyse |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/ehansih/universal-ai-gateway
cd universal-ai-gateway
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API keys
```bash
cp .env.example .env
```
Edit `.env` and fill in your keys:
```
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
OLLAMA_URL=http://localhost:11434
```
> You don't need all keys — the gateway works with whatever is available.

### 4. Run
```bash
python3 ui/app.py
```
Open **http://localhost:5000** in your browser.

---

## Free Option — Ollama (No API key needed)

Run AI models locally for free using [Ollama](https://ollama.com):

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Gateway will auto-detect it
```

---

## Project Structure

```
universal-ai-gateway/
├── gateway/
│   ├── agents/
│   │   ├── base.py          # Abstract base class for all agents
│   │   ├── claude.py        # Claude (Anthropic)
│   │   ├── openai_agent.py  # ChatGPT (OpenAI)
│   │   ├── gemini.py        # Gemini (Google)
│   │   └── ollama.py        # Ollama (local, free)
│   ├── router.py            # Smart task routing
│   ├── collaborator.py      # MACP collaboration logic
│   └── core.py              # Main gateway class
├── ui/
│   ├── app.py               # Flask web server
│   └── templates/
│       └── index.html       # Chat web UI
├── .env.example             # API key template
├── requirements.txt
└── README.md
```

---

## Adding a New AI Agent

Create a file in `gateway/agents/`:

```python
from .base import BaseAgent, AgentResponse

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyAI", "my-model-v1")

    def check_availability(self) -> bool:
        # check if API key exists and works
        self.available = True
        return True

    def ask(self, prompt: str) -> AgentResponse:
        # call your AI API here
        return AgentResponse(
            agent_name=self.name,
            model=self.model,
            content="response here",
            success=True
        )
```

Then add it to `gateway/core.py`:
```python
from .agents import MyNewAgent
self.agents.append(MyNewAgent())
```

---

## Related

- [macp-protocol](https://github.com/ehansih/macp-protocol) — MACP spec and AXON-1 language
- [whatsapp-auto-reply](https://github.com/ehansih/whatsapp-auto-reply) — WhatsApp auto-reply Android app

---

## License

MIT
