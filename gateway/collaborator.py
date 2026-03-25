"""
MACP Collaborator — agents debate and produce the best answer
"""
from typing import List
from .agents.base import BaseAgent, AgentResponse


def collaborate(question: str, agents: List[BaseAgent]) -> dict:
    available = [a for a in agents if a.available]

    if len(available) == 0:
        return {"error": "No agents available"}

    if len(available) == 1:
        resp = available[0].ask(question)
        return {
            "mode": "single",
            "rounds": [{"agent": resp.agent_name, "content": resp.content}],
            "final": resp.content
        }

    rounds = []

    # ROUND 1 — First agent answers independently
    agent_a = available[0]
    r1 = agent_a.ask(f"Answer this question thoroughly:\n\n{question}")
    rounds.append({"round": 1, "agent": agent_a.name, "content": r1.content, "success": r1.success})

    if not r1.success:
        return {"mode": "failed", "rounds": rounds, "final": f"Error: {r1.error}"}

    # ROUND 2 — Second agent critiques and enhances
    agent_b = available[1]
    critique_prompt = f"""The user asked: "{question}"

Another AI answered:
{r1.content}

Your job:
1. Point out anything incorrect or missing
2. Add anything important that was not mentioned
3. Keep what was correct
Give your enhanced version only."""

    r2 = agent_b.ask(critique_prompt)
    rounds.append({"round": 2, "agent": agent_b.name, "content": r2.content, "success": r2.success})

    if not r2.success:
        return {"mode": "partial", "rounds": rounds, "final": r1.content}

    # ROUND 3 — First agent synthesizes final answer
    synthesis_prompt = f"""The user asked: "{question}"

Your initial answer:
{r1.content}

A second AI reviewed and added:
{r2.content}

Now produce the FINAL best answer:
- Keep what both agreed on
- Resolve conflicts using best judgement
- Incorporate valid additions
- Be clear and structured
Do NOT mention that multiple AIs were involved."""

    r3 = agent_a.ask(synthesis_prompt)
    rounds.append({"round": 3, "agent": f"{agent_a.name} (synthesis)", "content": r3.content, "success": r3.success})

    return {
        "mode": "collaboration",
        "agents_used": [a.name for a in available[:2]],
        "rounds": rounds,
        "final": r3.content if r3.success else r1.content
    }
