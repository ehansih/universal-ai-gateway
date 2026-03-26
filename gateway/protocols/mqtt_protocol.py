"""
MQTT Protocol
Lightweight publish/subscribe for IoT and edge AI agents
Used when AI runs on embedded devices, sensors, edge nodes
"""
import os
import json
import time
import threading
from typing import List, Dict, Callable, Optional
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class MQTTProtocol(BaseProtocol):
    """
    MQTT-based AI agent communication
    Topics:
      ai/gateway/request   — send questions
      ai/gateway/response  — receive answers
      ai/agents/+/status   — agent status broadcasts
      ai/agents/+/result   — agent results
    """

    TOPIC_REQUEST  = "ai/gateway/request"
    TOPIC_RESPONSE = "ai/gateway/response"
    TOPIC_STATUS   = "ai/agents/+/status"

    def __init__(self):
        super().__init__("MQTT")
        self.broker   = os.getenv("MQTT_BROKER", "localhost")
        self.port     = int(os.getenv("MQTT_PORT", "1883"))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        self._client  = None
        self._responses: Dict[str, str] = {}
        self._callbacks: List[Callable] = []

    def check_availability(self) -> bool:
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client(client_id="gateway-check")
            if self.username:
                client.username_pw_set(self.username, self.password)
            client.connect(self.broker, self.port, keepalive=3)
            client.disconnect()
            self.status = ProtocolStatus.AVAILABLE
            return True
        except ImportError:
            self.status = ProtocolStatus.NOT_CONFIGURED
            return False
        except Exception:
            self.status = ProtocolStatus.UNAVAILABLE
            return False

    def connect(self):
        """Connect to MQTT broker and subscribe to response topic"""
        import paho.mqtt.client as mqtt

        self._client = mqtt.Client(client_id="universal-ai-gateway")
        if self.username:
            self._client.username_pw_set(self.username, self.password)

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                req_id = payload.get("request_id")
                if req_id:
                    self._responses[req_id] = payload.get("content", "")
                for cb in self._callbacks:
                    cb(msg.topic, payload)
            except Exception:
                pass

        self._client.on_message = on_message
        self._client.connect(self.broker, self.port)
        self._client.subscribe(self.TOPIC_RESPONSE)
        self._client.loop_start()

    def publish_request(self, question: str, request_id: str):
        """Publish an AI request to MQTT"""
        if not self._client:
            self.connect()
        payload = json.dumps({
            "request_id": request_id,
            "question": question,
            "timestamp": time.time()
        })
        self._client.publish(self.TOPIC_REQUEST, payload)

    def wait_for_response(self, request_id: str, timeout: int = 30) -> Optional[str]:
        """Wait for a response on the response topic"""
        start = time.time()
        while time.time() - start < timeout:
            if request_id in self._responses:
                return self._responses.pop(request_id)
            time.sleep(0.1)
        return None

    def broadcast_status(self, agent_name: str, status: Dict):
        """Broadcast agent status to all subscribers"""
        if not self._client:
            self.connect()
        topic = f"ai/agents/{agent_name}/status"
        self._client.publish(topic, json.dumps(status))

    def on_request(self, callback: Callable):
        """Register callback for incoming requests"""
        self._callbacks.append(callback)

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        last_msg = messages[-1].content if messages else ""

        if self.status != ProtocolStatus.AVAILABLE:
            return ProtocolResponse(
                protocol_name=self.name,
                content=f"MQTT broker not available at {self.broker}:{self.port}.\nSet MQTT_BROKER env var to connect.",
                success=False,
                error="MQTT not connected"
            )

        try:
            import uuid
            req_id = str(uuid.uuid4())
            self.publish_request(last_msg, req_id)
            response = self.wait_for_response(req_id, timeout=30)

            if response:
                return ProtocolResponse(
                    protocol_name=self.name,
                    content=response,
                    success=True,
                    metadata={"broker": self.broker, "protocol": "MQTT"}
                )
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error="Timeout waiting for MQTT response"
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
