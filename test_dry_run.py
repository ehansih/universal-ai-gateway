"""
Dry run test for Universal AI Gateway
Tests all components without real API calls using mock agents
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gateway.agents.base import BaseAgent, AgentResponse
from gateway.router import detect_task_type, pick_best_agent
from gateway.collaborator import collaborate

# ── Mock Agents ────────────────────────────────────────────────────────────────

class MockClaude(BaseAgent):
    def __init__(self):
        super().__init__("Claude", "mock-claude")
        self.available = True

    def check_availability(self): return True

    def ask(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            model=self.model,
            content=f"[Claude] Python is excellent for 2025 due to AI/ML dominance, simplicity, and vast ecosystem.",
            success=True,
            confidence=0.9
        )


class MockChatGPT(BaseAgent):
    def __init__(self):
        super().__init__("ChatGPT", "mock-gpt4o")
        self.available = True

    def check_availability(self): return True

    def ask(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            model=self.model,
            content=f"[ChatGPT] Agree on Python, but Rust and TypeScript are also rising fast in 2025 for systems and web.",
            success=True,
            confidence=0.85
        )


class MockGemini(BaseAgent):
    def __init__(self):
        super().__init__("Gemini", "mock-gemini")
        self.available = True

    def check_availability(self): return True

    def ask(self, prompt: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            model=self.model,
            content=f"[Gemini] Based on latest trends: Python #1, followed by JavaScript and Go.",
            success=True,
            confidence=0.88
        )


class MockOllama(BaseAgent):
    def __init__(self):
        super().__init__("Ollama/llama3", "llama3")
        self.available = False  # Simulating offline

    def check_availability(self): return False

    def ask(self, prompt: str) -> AgentResponse:
        return AgentResponse(agent_name=self.name, model=self.model, content="", success=False, error="Offline")


# ── Test Helpers ───────────────────────────────────────────────────────────────

PASS = "  ✓ PASS"
FAIL = "  ✗ FAIL"
tests_run = 0
tests_passed = 0


def test(name: str, condition: bool, detail: str = ""):
    global tests_run, tests_passed
    tests_run += 1
    if condition:
        tests_passed += 1
        print(f"{PASS} | {name}")
    else:
        print(f"{FAIL} | {name}" + (f" → {detail}" if detail else ""))


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_agent_responses():
    print("\n── TEST 1: Agent Responses ─────────────────────────────────────")
    agents = [MockClaude(), MockChatGPT(), MockGemini(), MockOllama()]

    for agent in agents[:3]:
        resp = agent.ask("test question")
        test(f"{agent.name} returns success", resp.success)
        test(f"{agent.name} has content", len(resp.content) > 0)

    # Ollama should fail
    resp = MockOllama().ask("test")
    test("Ollama offline returns failure", not resp.success)


def test_task_detection():
    print("\n── TEST 2: Task Type Detection ─────────────────────────────────")
    cases = [
        ("Write me a Python function to sort a list", "code"),
        ("Calculate the square root of 144", "math"),
        ("Write a poem about the ocean", "creative"),
        ("What are the latest AI news today?", "search"),
        ("Why is the sky blue? Explain.", "reason"),
        ("Hello how are you", "general"),
    ]
    for question, expected in cases:
        detected = detect_task_type(question)
        test(f'"{question[:40]}..." → {expected}', detected == expected, f"got: {detected}")


def test_smart_routing():
    print("\n── TEST 3: Smart Routing ───────────────────────────────────────")
    agents = [MockClaude(), MockChatGPT(), MockGemini(), MockOllama()]
    available = [a for a in agents if a.available]

    code_q = "Write a Python function to reverse a string"
    best = pick_best_agent(code_q, available)
    test("Code question → Claude", best.name == "Claude", f"got: {best.name}")

    math_q = "Calculate compound interest formula"
    best = pick_best_agent(math_q, available)
    test("Math question → ChatGPT", best.name == "ChatGPT", f"got: {best.name}")

    search_q = "What is the latest news about AI today?"
    best = pick_best_agent(search_q, available)
    test("Search question → Gemini", best.name == "Gemini", f"got: {best.name}")


def test_fallback():
    print("\n── TEST 4: Fallback Handling ────────────────────────────────────")
    # Only Ollama available (offline) — should return None or handle gracefully
    agents = [MockOllama()]
    available = [a for a in agents if a.available]
    test("No available agents returns empty list", len(available) == 0)

    # Only one agent available
    agents = [MockClaude()]
    result = collaborate("test question", agents)
    test("Single agent collaboration works", result.get("mode") == "single")
    test("Single agent returns content", len(result.get("final", "")) > 0)


def test_collaboration():
    print("\n── TEST 5: MACP Collaboration ──────────────────────────────────")
    agents = [MockClaude(), MockChatGPT()]
    result = collaborate("What is the best programming language in 2025?", agents)

    test("Collaboration mode is set", result.get("mode") == "collaboration")
    test("Has 3 rounds", len(result.get("rounds", [])) == 3)
    test("Round 1 is Claude", result["rounds"][0]["agent"] == "Claude")
    test("Round 2 is ChatGPT", result["rounds"][1]["agent"] == "ChatGPT")
    test("Final answer exists", len(result.get("final", "")) > 0)
    test("Agents used tracked", len(result.get("agents_used", [])) == 2)


def test_all_agents():
    print("\n── TEST 6: Ask All Agents ──────────────────────────────────────")
    agents = [MockClaude(), MockChatGPT(), MockGemini(), MockOllama()]
    available = [a for a in agents if a.available]

    responses = []
    for agent in available:
        resp = agent.ask("What is AI?")
        responses.append(resp)

    test("3 agents available (Ollama offline)", len(available) == 3)
    test("All available agents responded", all(r.success for r in responses))
    test("All responses have content", all(len(r.content) > 0 for r in responses))


def test_agent_metadata():
    print("\n── TEST 7: Agent Metadata ──────────────────────────────────────")
    c = MockClaude()
    test("Claude name is correct", c.name == "Claude")
    test("Claude available", c.available == True)
    test("Claude repr contains name", "Claude" in repr(c))

    o = MockOllama()
    test("Ollama unavailable", o.available == False)
    test("Ollama repr shows ✗", "✗" in repr(o))


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" Universal AI Gateway — Dry Run Test")
    print("=" * 60)

    test_agent_responses()
    test_task_detection()
    test_smart_routing()
    test_fallback()
    test_collaboration()
    test_all_agents()
    test_agent_metadata()

    print("\n" + "=" * 60)
    print(f" Results: {tests_passed}/{tests_run} tests passed")
    if tests_passed == tests_run:
        print(" ALL TESTS PASSED ✓")
    else:
        print(f" {tests_run - tests_passed} TESTS FAILED ✗")
    print("=" * 60)

    sys.exit(0 if tests_passed == tests_run else 1)
