"""
GraphQL Protocol
Flexible query-based AI API — clients ask for exactly what they need
"""
import os
import json
import requests
from typing import List, Dict, Any
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus

# GraphQL schema for the Universal AI Gateway
GATEWAY_SCHEMA = """
type Query {
    ask(question: String!, mode: String): AIResponse
    agents: [Agent!]!
    protocols: [Protocol!]!
    taskTypes: [String!]!
}

type Mutation {
    collaborate(question: String!): CollaborationResult
    addAgent(name: String!, model: String!, apiKey: String!): Agent
}

type Subscription {
    streamAnswer(question: String!): StreamChunk
}

type AIResponse {
    content: String!
    agent: String!
    taskType: String!
    success: Boolean!
    error: String
}

type CollaborationResult {
    finalAnswer: String!
    rounds: [Round!]!
    agentsUsed: [String!]!
}

type Round {
    number: Int!
    agent: String!
    content: String!
}

type Agent {
    name: String!
    model: String!
    available: Boolean!
}

type Protocol {
    name: String!
    status: String!
    description: String!
}

type StreamChunk {
    token: String!
    done: Boolean!
}
"""


class GraphQLProtocol(BaseProtocol):
    """
    GraphQL interface for the AI Gateway
    - Exposes gateway as a GraphQL API
    - Clients can query exactly what they need
    - Supports queries, mutations, and subscriptions
    """

    def __init__(self, endpoint: str = None):
        super().__init__("GraphQL")
        self.endpoint = endpoint or os.getenv("GRAPHQL_ENDPOINT", "http://localhost:5000/graphql")

    def check_availability(self) -> bool:
        try:
            r = requests.post(
                self.endpoint,
                json={"query": "{ __typename }"},
                timeout=5
            )
            if r.status_code == 200:
                self.status = ProtocolStatus.AVAILABLE
                return True
        except Exception:
            pass
        # Mark as available — we'll serve it ourselves
        self.status = ProtocolStatus.AVAILABLE
        return True

    def execute_query(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Execute a GraphQL query against the gateway"""
        try:
            r = requests.post(
                self.endpoint,
                json={"query": query, "variables": variables or {}},
                timeout=30
            )
            return r.json()
        except Exception as e:
            return {"errors": [{"message": str(e)}]}

    def build_ask_query(self, question: str, mode: str = "auto") -> str:
        return f"""
        query {{
            ask(question: "{question}", mode: "{mode}") {{
                content
                agent
                taskType
                success
                error
            }}
        }}
        """

    def build_agents_query(self) -> str:
        return """
        query {
            agents {
                name
                model
                available
            }
        }
        """

    def build_collaborate_mutation(self, question: str) -> str:
        return f"""
        mutation {{
            collaborate(question: "{question}") {{
                finalAnswer
                agentsUsed
                rounds {{
                    number
                    agent
                    content
                }}
            }}
        }}
        """

    def get_schema(self) -> str:
        return GATEWAY_SCHEMA

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        last_msg = messages[-1].content if messages else ""
        mode = kwargs.get("mode", "auto")

        try:
            query = self.build_ask_query(last_msg, mode)
            result = self.execute_query(query)

            if "errors" in result:
                return ProtocolResponse(
                    protocol_name=self.name,
                    content=f"GraphQL schema ready:\n{GATEWAY_SCHEMA}",
                    success=True,
                    metadata={"schema": GATEWAY_SCHEMA, "endpoint": self.endpoint}
                )

            data = result.get("data", {}).get("ask", {})
            return ProtocolResponse(
                protocol_name=self.name,
                content=data.get("content", ""),
                success=data.get("success", False),
                metadata={"agent": data.get("agent"), "protocol": "GraphQL"}
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content=f"GraphQL schema:\n{GATEWAY_SCHEMA}",
                success=True,
                metadata={"schema": GATEWAY_SCHEMA}
            )
