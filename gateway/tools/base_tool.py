"""
Tool use framework — agents can call external tools
"""
import math
import json
import os
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, input: str) -> str:
        pass

    def to_dict(self) -> Dict:
        return {"name": self.name, "description": self.description}


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__("calculator", "Evaluate mathematical expressions")

    def run(self, expression: str) -> str:
        try:
            allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            result = eval(expression, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"Error: {e}"


class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__("web_search", "Search the web for current information")

    def run(self, query: str) -> str:
        try:
            api_key = os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_KEY")
            if not api_key:
                return f"[Web search not configured — set SERPER_API_KEY]\nQuery was: {query}"
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query},
                timeout=10
            )
            results = r.json().get("organic", [])[:3]
            return "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)
        except Exception as e:
            return f"Search error: {e}"


class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__("weather", "Get current weather for a location")

    def run(self, location: str) -> str:
        try:
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                return f"[Weather not configured — set OPENWEATHER_API_KEY]\nLocation: {location}"
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": location, "appid": api_key, "units": "metric"},
                timeout=10
            )
            data = r.json()
            return f"{location}: {data['weather'][0]['description']}, {data['main']['temp']}°C"
        except Exception as e:
            return f"Weather error: {e}"


class ToolRegistry:
    """Registry of all available tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # Register default tools
        for tool in [CalculatorTool(), WebSearchTool(), WeatherTool()]:
            self.register(tool)

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        return [t.to_dict() for t in self._tools.values()]

    def run(self, tool_name: str, input: str) -> str:
        tool = self.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found"
        return tool.run(input)

    def detect_and_run(self, question: str) -> Dict[str, str]:
        """Auto-detect if question needs a tool and run it"""
        results = {}
        q = question.lower()

        if any(w in q for w in ["calculate", "compute", "math", "sqrt", "+"]):
            expr = question.split("calculate")[-1].strip() if "calculate" in q else question
            results["calculator"] = self.run("calculator", expr)

        if any(w in q for w in ["weather", "temperature", "forecast"]):
            results["weather"] = self.run("weather", question)

        if any(w in q for w in ["search", "latest", "news", "today", "current"]):
            results["web_search"] = self.run("web_search", question)

        return results
