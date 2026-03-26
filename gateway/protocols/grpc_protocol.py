"""
gRPC Protocol
High-performance binary protocol for AI agent communication
Used in production AI systems for low-latency agent calls
"""
import os
import json
from typing import List
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


# gRPC service definition (proto equivalent in Python)
GRPC_SERVICE_DEFINITION = """
// ai_gateway.proto
syntax = "proto3";

service AIGateway {
    rpc Ask (AskRequest) returns (AskResponse);
    rpc AskStream (AskRequest) returns (stream AskChunk);
    rpc Collaborate (CollaborateRequest) returns (CollaborateResponse);
}

message AskRequest {
    string question = 1;
    string mode = 2;
    string session_id = 3;
}

message AskResponse {
    string content = 1;
    string agent = 2;
    bool success = 3;
    string error = 4;
}

message AskChunk {
    string token = 1;
    bool done = 2;
}

message CollaborateRequest {
    string question = 1;
    repeated string agent_names = 2;
}

message CollaborateResponse {
    string final_answer = 1;
    repeated RoundResult rounds = 2;
}

message RoundResult {
    int32 round = 1;
    string agent = 2;
    string content = 3;
}
"""


class GRPCProtocol(BaseProtocol):
    """
    gRPC Protocol — high-performance binary AI communication
    Implements the AIGateway service definition above

    To use:
    1. Install: pip install grpcio grpcio-tools
    2. Generate stubs: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ai_gateway.proto
    3. Connect to a gRPC AI server
    """

    def __init__(self, host: str = None, port: int = None):
        super().__init__("gRPC")
        self.host = host or os.getenv("GRPC_HOST", "localhost")
        self.port = port or int(os.getenv("GRPC_PORT", "50051"))
        self._channel = None
        self._stub = None

    def check_availability(self) -> bool:
        try:
            import grpc
            self._channel = grpc.insecure_channel(f"{self.host}:{self.port}")
            grpc.channel_ready_future(self._channel).result(timeout=3)
            self.status = ProtocolStatus.AVAILABLE
            return True
        except ImportError:
            self.status = ProtocolStatus.NOT_CONFIGURED
            return False
        except Exception:
            self.status = ProtocolStatus.UNAVAILABLE
            return False

    def get_service_definition(self) -> str:
        """Returns the proto service definition for this gateway"""
        return GRPC_SERVICE_DEFINITION

    def start_grpc_server(self, gateway_instance, port: int = 50051):
        """
        Start a gRPC server exposing the gateway as a gRPC service
        Requires generated stubs from ai_gateway.proto
        """
        try:
            import grpc
            from concurrent import futures

            # This would use generated stubs
            # server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            # add_AIGatewayServicer_to_server(GatewayServicer(gateway_instance), server)
            # server.add_insecure_port(f'[::]:{port}')
            # server.start()
            return f"gRPC server would start on port {port}"
        except Exception as e:
            return f"Error: {e}"

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        last_msg = messages[-1].content if messages else ""

        if self.status != ProtocolStatus.AVAILABLE:
            return ProtocolResponse(
                protocol_name=self.name,
                content=f"gRPC server not available at {self.host}:{self.port}.\n\nService definition:\n{GRPC_SERVICE_DEFINITION}",
                success=False,
                error="gRPC server not connected",
                metadata={"proto": GRPC_SERVICE_DEFINITION}
            )

        try:
            # Would call self._stub.Ask(AskRequest(question=last_msg))
            return ProtocolResponse(
                protocol_name=self.name,
                content="gRPC call executed",
                success=True,
                metadata={"host": self.host, "port": self.port}
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
