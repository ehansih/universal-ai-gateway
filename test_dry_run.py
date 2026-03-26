"""
Dry run test for Universal AI Gateway — all protocols, memory, tools
Uses mock agents and stubs — no real API calls
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from gateway.agents.base import BaseAgent, AgentResponse
from gateway.protocols.base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus
from gateway.router import detect_task_type, pick_best_agent
from gateway.collaborator import collaborate
from gateway.memory.conversation import ConversationMemory
from gateway.tools.base_tool import CalculatorTool, ToolRegistry

# ── Mock Agents ────────────────────────────────────────────────────────────────

class MockClaude(BaseAgent):
    def __init__(self):
        super().__init__("Claude", "mock-claude")
        self.available = True
    def check_availability(self): return True
    def ask(self, prompt): return AgentResponse("Claude", "mock-claude", "[Claude] Python is best for 2025 — AI/ML dominance.", True, confidence=0.9)

class MockChatGPT(BaseAgent):
    def __init__(self):
        super().__init__("ChatGPT", "mock-gpt4o")
        self.available = True
    def check_availability(self): return True
    def ask(self, prompt): return AgentResponse("ChatGPT", "mock-gpt4o", "[ChatGPT] Agree on Python, but Rust rising fast.", True, confidence=0.85)

class MockGemini(BaseAgent):
    def __init__(self):
        super().__init__("Gemini", "mock-gemini")
        self.available = True
    def check_availability(self): return True
    def ask(self, prompt): return AgentResponse("Gemini", "mock-gemini", "[Gemini] Python #1, JS and Go follow.", True, confidence=0.88)

class MockOllama(BaseAgent):
    def __init__(self):
        super().__init__("Ollama/llama3", "llama3")
        self.available = False
    def check_availability(self): return False
    def ask(self, prompt): return AgentResponse("Ollama/llama3", "llama3", "", False, "Offline")

# ── Mock Protocols ─────────────────────────────────────────────────────────────

class MockProtocol(BaseProtocol):
    def __init__(self, name, available=True):
        super().__init__(name)
        self.status = ProtocolStatus.AVAILABLE if available else ProtocolStatus.UNAVAILABLE
    def check_availability(self): return self.status == ProtocolStatus.AVAILABLE
    def send(self, messages, **kwargs):
        return ProtocolResponse(self.name, f"[{self.name}] Mock response", True, metadata={"protocol": self.name})

# ── Test Helpers ───────────────────────────────────────────────────────────────

passed = failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}" + (f" → {detail}" if detail else ""))

# ── Test Suites ────────────────────────────────────────────────────────────────

def test_agents():
    print("\n── 1. Agent Responses ──────────────────────────────────────────")
    for agent in [MockClaude(), MockChatGPT(), MockGemini()]:
        r = agent.ask("test")
        test(f"{agent.name} success", r.success)
        test(f"{agent.name} has content", len(r.content) > 0)
    r = MockOllama().ask("test")
    test("Ollama offline = failure", not r.success)

def test_routing():
    print("\n── 2. Smart Routing ────────────────────────────────────────────")
    cases = [
        ("Write a Python script", "code"),
        ("Calculate 2+2", "math"),
        ("Write a poem", "creative"),
        ("Latest AI news today", "search"),
        ("Why is the sky blue?", "reason"),
        ("Hello there", "general"),
    ]
    for q, expected in cases:
        detected = detect_task_type(q)
        test(f'"{q[:35]}..." → {expected}', detected == expected, f"got: {detected}")

    agents = [MockClaude(), MockChatGPT(), MockGemini()]
    test("Code → Claude",   pick_best_agent("write code", agents).name == "Claude")
    test("Math → ChatGPT",  pick_best_agent("calculate math", agents).name == "ChatGPT")
    test("Search → Gemini", pick_best_agent("latest news today", agents).name == "Gemini")

def test_collaboration():
    print("\n── 3. MACP Collaboration ───────────────────────────────────────")
    agents = [MockClaude(), MockChatGPT()]
    result = collaborate("Best language 2025?", agents)
    test("Mode = collaboration", result.get("mode") == "collaboration")
    test("3 rounds produced", len(result.get("rounds", [])) == 3)
    test("Round 1 = Claude",   result["rounds"][0]["agent"] == "Claude")
    test("Round 2 = ChatGPT",  result["rounds"][1]["agent"] == "ChatGPT")
    test("Final answer exists", len(result.get("final", "")) > 0)
    test("Agents tracked", len(result.get("agents_used", [])) == 2)

    # Single agent fallback
    r2 = collaborate("test", [MockClaude()])
    test("Single agent = single mode", r2.get("mode") == "single")

    # No agents
    r3 = collaborate("test", [])
    test("No agents = error", "error" in r3)

def test_protocols():
    print("\n── 4. Protocol Layer ───────────────────────────────────────────")
    proto_names = ["MCP", "A2A", "ACP", "OpenAI-Assistants", "LangChain", "AutoGen", "WebSocket-Stream", "gRPC", "MQTT", "GraphQL"]
    for name in proto_names:
        p = MockProtocol(name)
        r = p.send([ProtocolMessage("user", "test question")])
        test(f"{name}: returns response", r.success)
        test(f"{name}: has content", len(r.content) > 0)
        test(f"{name}: protocol name set", r.protocol_name == name)

    # Unavailable protocol
    p_off = MockProtocol("gRPC", available=False)
    test("Unavailable protocol status", p_off.status == ProtocolStatus.UNAVAILABLE)

def test_memory():
    print("\n── 5. Conversation Memory ──────────────────────────────────────")
    mem = ConversationMemory(storage_path="/tmp/test_conversations.json")

    mem.add("sess1", "user", "Hello!")
    mem.add("sess1", "assistant", "Hi there!", agent="Claude")
    mem.add("sess2", "user", "Different session")

    turns = mem.get("sess1")
    test("Session 1 has 2 turns", len(turns) == 2)
    test("First turn is user", turns[0].role == "user")
    test("Second turn has agent", turns[1].agent == "Claude")

    context = mem.get_context("sess1")
    test("Context contains USER:", "USER:" in context)

    sessions = mem.list_sessions()
    test("Two sessions exist", len(sessions) == 2)

    mem.clear("sess1")
    test("Session cleared", len(mem.get("sess1")) == 0)

    mem.clear_all()
    test("All sessions cleared", len(mem.list_sessions()) == 0)

    if os.path.exists("/tmp/test_conversations.json"):
        os.remove("/tmp/test_conversations.json")

def test_tools():
    print("\n── 6. Tool Registry ────────────────────────────────────────────")
    calc = CalculatorTool()
    test("Calculator 2+2 = 4",    calc.run("2+2") == "4")
    test("Calculator 10*5 = 50",  calc.run("10*5") == "50")
    test("Calculator sqrt(16)",   calc.run("sqrt(16)") == "4.0")
    test("Calculator bad input",  "Error" in calc.run("__import__('os')"))

    registry = ToolRegistry()
    tools = registry.list_tools()
    test("Registry has 3 tools",  len(tools) == 3)
    tool_names = [t["name"] for t in tools]
    test("Calculator in registry", "calculator" in tool_names)
    test("Web search in registry", "web_search" in tool_names)
    test("Weather in registry",    "weather" in tool_names)

    result = registry.run("calculator", "5*5")
    test("Registry runs calculator", result == "25")

    detected = registry.detect_and_run("calculate 2+2")
    test("Auto-detect calculator", "calculator" in detected)

def test_a2a_agent_card():
    print("\n── 7. A2A Agent Card ────────────────────────────────────────────")
    from gateway.protocols.a2a_protocol import A2AProtocol, AgentCard
    card = AgentCard("TestAgent", "http://localhost:5000", "Test", ["qa", "code"])
    d = card.to_dict()
    test("Agent card has name",   d["name"] == "TestAgent")
    test("Agent card has url",    d["url"] == "http://localhost:5000")
    test("Agent card has skills", len(d["skills"]) == 2)
    test("Agent card is valid JSON", len(card.to_json()) > 0)

def test_graphql_schema():
    print("\n── 8. GraphQL Schema ────────────────────────────────────────────")
    from gateway.protocols.graphql_protocol import GATEWAY_SCHEMA
    test("Schema has Query",        "type Query" in GATEWAY_SCHEMA)
    test("Schema has Mutation",     "type Mutation" in GATEWAY_SCHEMA)
    test("Schema has Subscription", "type Subscription" in GATEWAY_SCHEMA)
    test("Schema has ask field",    "ask(" in GATEWAY_SCHEMA)
    test("Schema has collaborate",  "collaborate" in GATEWAY_SCHEMA)
    test("Schema has streaming",    "StreamChunk" in GATEWAY_SCHEMA)

def test_grpc_definition():
    print("\n── 9. gRPC Service Definition ──────────────────────────────────")
    from gateway.protocols.grpc_protocol import GRPC_SERVICE_DEFINITION
    test("Proto has service",     "service AIGateway" in GRPC_SERVICE_DEFINITION)
    test("Proto has Ask rpc",     "rpc Ask" in GRPC_SERVICE_DEFINITION)
    test("Proto has stream rpc",  "AskStream" in GRPC_SERVICE_DEFINITION)
    test("Proto has Collaborate", "Collaborate" in GRPC_SERVICE_DEFINITION)
    test("Proto has messages",    "message AskRequest" in GRPC_SERVICE_DEFINITION)

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" Universal AI Gateway — Full Dry Run Test")
    print("=" * 60)

    test_agents()
    test_routing()
    test_collaboration()
    test_protocols()
    test_memory()
    test_tools()
    test_a2a_agent_card()
    test_graphql_schema()
    test_grpc_definition()

    total = passed + failed
    print(f"\n{'='*60}")
    print(f" Results: {passed}/{total} tests passed")
    print(" ALL TESTS PASSED ✓" if failed == 0 else f" {failed} TESTS FAILED ✗")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
