# Universal AI Gateway

A unified gateway that connects to all major AI agents — Claude, ChatGPT, Gemini, and local models via Ollama — and lets them collaborate using the **MACP (Multi-Agent Collaboration Protocol)**. Supports every major AI-to-AI communication protocol known as of 2026.

---

## What it does

Instead of asking multiple AIs separately:

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

## Supported AI Agents

| Agent | Model | Requires |
|-------|-------|---------|
| Claude | claude-sonnet-4-6 | Anthropic API key |
| ChatGPT | gpt-4o | OpenAI API key |
| Gemini | gemini-1.5-pro | Google API key |
| Ollama | llama3 (or any) | Local Ollama install (free) |

---

## Supported Protocols (10)

| Protocol | Description | Status |
|----------|-------------|--------|
| **MCP** | Model Context Protocol — connect AI to tools/files/databases (Anthropic) | REST/JSON-RPC |
| **A2A** | Agent-to-Agent — agent discovery and delegation (Google 2025) | HTTP + Agent Cards |
| **ACP** | Agent Communication Protocol — REST-based agent communication (IBM/Linux Foundation) | REST |
| **OpenAI Assistants** | Stateful agents with memory, file access, code execution | OpenAI API |
| **LangChain** | Chain-based agents with tools and memory pipelines | Python |
| **AutoGen** | Multi-agent group conversations (Microsoft) | Python |
| **WebSocket/SSE** | Real-time token streaming | Server-Sent Events |
| **gRPC** | High-performance binary protocol for production AI systems | Protobuf |
| **MQTT** | Lightweight pub/sub for IoT and edge AI agents | Broker |
| **GraphQL** | Flexible query API — ask for exactly what you need | HTTP |

---

## Features

- **Auto Mode** — detects task type (code, math, creative, search, reason) and routes to best AI
- **Collaborate Mode** — MACP 3-round debate between AIs, produces unified best answer
- **Ask All Mode** — sends question to all available AIs, shows all answers
- **Stream Mode** — real-time token streaming via SSE
- **Protocol Mode** — talk directly via any of the 10 supported protocols
- **Conversation Memory** — persistent history across sessions
- **Tool Use** — calculator, web search, weather auto-detected from question
- **A2A Agent Card** — gateway is discoverable by other A2A agents at `/.well-known/agent.json`
- **GraphQL API** — full schema exposed at `/graphql`
- **Web UI** — dark-themed chat interface with protocol selector

---

## MACP — Multi-Agent Collaboration Protocol

3-round debate between AI agents:

```
ROUND 1 — Claude answers independently
ROUND 2 — ChatGPT critiques and enhances Claude's answer
ROUND 3 — Claude synthesizes both into the final best answer
OUTPUT  — Single best answer
```

Uses **AXON-1** message encoding:
```
[CMD] > [SUBJECT] : [PREDICATE] ~ [CONTEXT] | [CONFIDENCE]

AGENT_1 >> AGENT_2 : @QRY : BEST_ROUTE ~ LOC:DELHI>MUMBAI | TIME:NOW !!
AGENT_2 >> AGENT_1 : @RSP : ROUTE~~NH48 | DURATION:14H | CONF:0.87
```

---

## Smart Routing

| Task Type | Best Agent | Trigger Keywords |
|-----------|-----------|-----------------|
| Code | Claude | code, script, bug, function, python |
| Math | ChatGPT | calculate, equation, solve, math |
| Creative | Claude | write, poem, story, essay |
| Search | Gemini | latest, news, today, recent, current |
| Reasoning | Claude | why, explain, compare, analyse |
| General | Claude | anything else |

---

## Project Structure

```
universal-ai-gateway/
├── gateway/
│   ├── agents/
│   │   ├── base.py              # Abstract base class for all agents
│   │   ├── claude.py            # Claude (Anthropic)
│   │   ├── openai_agent.py      # ChatGPT (OpenAI)
│   │   ├── gemini.py            # Gemini (Google)
│   │   └── ollama.py            # Ollama (local, free)
│   ├── protocols/
│   │   ├── base_protocol.py     # Abstract base class for all protocols
│   │   ├── mcp_protocol.py      # Model Context Protocol
│   │   ├── a2a_protocol.py      # Agent-to-Agent (Google)
│   │   ├── acp_protocol.py      # Agent Communication Protocol (IBM)
│   │   ├── openai_assistants.py # OpenAI Assistants API
│   │   ├── langchain_protocol.py# LangChain
│   │   ├── autogen_protocol.py  # AutoGen (Microsoft)
│   │   ├── websocket_protocol.py# WebSocket/SSE Streaming
│   │   ├── grpc_protocol.py     # gRPC
│   │   ├── mqtt_protocol.py     # MQTT
│   │   └── graphql_protocol.py  # GraphQL
│   ├── memory/
│   │   └── conversation.py      # Persistent conversation history
│   ├── tools/
│   │   └── base_tool.py         # Calculator, Web Search, Weather
│   ├── router.py                # Smart task routing
│   ├── collaborator.py          # MACP collaboration logic
│   └── core.py                  # Main gateway class
├── ui/
│   ├── app.py                   # Flask web server
│   └── templates/
│       └── index.html           # Chat web UI
├── test_dry_run.py              # 87/87 tests passing
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/ehansih/universal-ai-gateway
cd universal-ai-gateway
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
python3 ui/app.py
```

Open **http://localhost:5000**

---

## Environment Variables

```env
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
OLLAMA_URL=http://localhost:11434

# Optional protocols
MCP_SERVER_URL=http://localhost:3000
ACP_SERVER_URL=http://localhost:8080
MQTT_BROKER=localhost
MQTT_PORT=1883
GRPC_HOST=localhost
GRPC_PORT=50051
GATEWAY_URL=http://localhost:5000
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/ask` | POST | Ask a question (all modes) |
| `/stream` | GET | SSE streaming response |
| `/status` | GET | Gateway status — agents and protocols |
| `/history/<session_id>` | GET | Conversation history |
| `/tools` | GET | List available tools |
| `/tool/run` | POST | Run a specific tool |
| `/.well-known/agent.json` | GET | A2A Agent Card |
| `/graphql` | POST/GET | GraphQL endpoint |

---

## Adding a New Agent

```python
# gateway/agents/my_agent.py
from .base import BaseAgent, AgentResponse

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyAI", "my-model")

    def check_availability(self):
        self.available = True
        return True

    def ask(self, prompt):
        return AgentResponse(self.name, self.model, "response", True)
```

Add to `gateway/core.py`:
```python
from .agents import MyAgent
self.agents.append(MyAgent())
```

---

## Adding a New Protocol

```python
# gateway/protocols/my_protocol.py
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus

class MyProtocol(BaseProtocol):
    def __init__(self):
        super().__init__("MyProtocol")

    def check_availability(self):
        self.status = ProtocolStatus.AVAILABLE
        return True

    def send(self, messages, **kwargs):
        return ProtocolResponse(self.name, "response", True)
```

---

## Test Results

Full dry run — all 87 tests passing. No real API calls required.

```
============================================================
 Universal AI Gateway — Full Dry Run Test
============================================================

── 1. Agent Responses ──────────────────────────────────────────
  ✓ Claude success
  ✓ Claude has content
  ✓ ChatGPT success
  ✓ ChatGPT has content
  ✓ Gemini success
  ✓ Gemini has content
  ✓ Ollama offline = failure

── 2. Smart Routing ────────────────────────────────────────────
  ✓ "Write a Python script..." → code
  ✓ "Calculate 2+2..." → math
  ✓ "Write a poem..." → creative
  ✓ "Latest AI news today..." → search
  ✓ "Why is the sky blue?..." → reason
  ✓ "Hello there..." → general
  ✓ Code → Claude
  ✓ Math → ChatGPT
  ✓ Search → Gemini

── 3. MACP Collaboration ───────────────────────────────────────
  ✓ Mode = collaboration
  ✓ 3 rounds produced
  ✓ Round 1 = Claude
  ✓ Round 2 = ChatGPT
  ✓ Final answer exists
  ✓ Agents tracked
  ✓ Single agent = single mode
  ✓ No agents = error

── 4. Protocol Layer ───────────────────────────────────────────
  ✓ MCP: returns response
  ✓ MCP: has content
  ✓ MCP: protocol name set
  ✓ A2A: returns response
  ✓ A2A: has content
  ✓ A2A: protocol name set
  ✓ ACP: returns response
  ✓ ACP: has content
  ✓ ACP: protocol name set
  ✓ OpenAI-Assistants: returns response
  ✓ OpenAI-Assistants: has content
  ✓ OpenAI-Assistants: protocol name set
  ✓ LangChain: returns response
  ✓ LangChain: has content
  ✓ LangChain: protocol name set
  ✓ AutoGen: returns response
  ✓ AutoGen: has content
  ✓ AutoGen: protocol name set
  ✓ WebSocket-Stream: returns response
  ✓ WebSocket-Stream: has content
  ✓ WebSocket-Stream: protocol name set
  ✓ gRPC: returns response
  ✓ gRPC: has content
  ✓ gRPC: protocol name set
  ✓ MQTT: returns response
  ✓ MQTT: has content
  ✓ MQTT: protocol name set
  ✓ GraphQL: returns response
  ✓ GraphQL: has content
  ✓ GraphQL: protocol name set
  ✓ Unavailable protocol status

── 5. Conversation Memory ──────────────────────────────────────
  ✓ Session 1 has 2 turns
  ✓ First turn is user
  ✓ Second turn has agent
  ✓ Context contains USER:
  ✓ Two sessions exist
  ✓ Session cleared
  ✓ All sessions cleared

── 6. Tool Registry ────────────────────────────────────────────
  ✓ Calculator 2+2 = 4
  ✓ Calculator 10*5 = 50
  ✓ Calculator sqrt(16)
  ✓ Calculator bad input
  ✓ Registry has 3 tools
  ✓ Calculator in registry
  ✓ Web search in registry
  ✓ Weather in registry
  ✓ Registry runs calculator
  ✓ Auto-detect calculator

── 7. A2A Agent Card ────────────────────────────────────────────
  ✓ Agent card has name
  ✓ Agent card has url
  ✓ Agent card has skills
  ✓ Agent card is valid JSON

── 8. GraphQL Schema ────────────────────────────────────────────
  ✓ Schema has Query
  ✓ Schema has Mutation
  ✓ Schema has Subscription
  ✓ Schema has ask field
  ✓ Schema has collaborate
  ✓ Schema has streaming

── 9. gRPC Service Definition ──────────────────────────────────
  ✓ Proto has service
  ✓ Proto has Ask rpc
  ✓ Proto has stream rpc
  ✓ Proto has Collaborate
  ✓ Proto has messages

============================================================
 Results: 87/87 tests passed
 ALL TESTS PASSED ✓
============================================================
```

To run tests yourself:
```bash
python3 test_dry_run.py
```

---

## Related

- [macp-protocol](https://github.com/ehansih/macp-protocol) — MACP spec and AXON-1 language
- [whatsapp-auto-reply](https://github.com/ehansih/whatsapp-auto-reply) — WhatsApp auto-reply Android app

---

## License

MIT
