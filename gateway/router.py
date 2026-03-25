"""
Smart router — picks the best agent for a given task
"""
from typing import List
from .agents.base import BaseAgent

TASK_KEYWORDS = {
    "code":    ["code", "script", "function", "bug", "program", "python", "javascript", "debug"],
    "math":    ["calculate", "math", "equation", "solve", "number", "formula"],
    "creative":["write", "poem", "story", "creative", "imagine", "essay"],
    "search":  ["latest", "recent", "news", "today", "current", "2024", "2025", "2026"],
    "reason":  ["why", "explain", "reason", "analyse", "compare", "difference"],
}

# Which agent is best for each task type
AGENT_PREFERENCE = {
    "code":     ["Claude", "ChatGPT", "Ollama/llama3", "Gemini"],
    "math":     ["ChatGPT", "Claude", "Gemini", "Ollama/llama3"],
    "creative": ["Claude", "ChatGPT", "Gemini", "Ollama/llama3"],
    "search":   ["Gemini", "ChatGPT", "Claude", "Ollama/llama3"],
    "reason":   ["Claude", "ChatGPT", "Gemini", "Ollama/llama3"],
    "general":  ["Claude", "ChatGPT", "Gemini", "Ollama/llama3"],
}


def detect_task_type(question: str) -> str:
    q = question.lower()
    for task, keywords in TASK_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return task
    return "general"


def pick_best_agent(question: str, available_agents: List[BaseAgent]) -> BaseAgent:
    task = detect_task_type(question)
    preference = AGENT_PREFERENCE.get(task, AGENT_PREFERENCE["general"])
    available_names = {a.name: a for a in available_agents if a.available}

    for preferred in preference:
        if preferred in available_names:
            return available_names[preferred]

    # fallback: return first available
    return available_agents[0] if available_agents else None
