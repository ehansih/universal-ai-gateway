import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from gateway import UniversalAIGateway

app = Flask(__name__)
gateway = UniversalAIGateway()


@app.route("/")
def index():
    return render_template("index.html", status=gateway.status())


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "").strip()
    mode = data.get("mode", "auto")
    session_id = data.get("session_id", "default")
    if not question:
        return jsonify({"error": "No question provided"}), 400
    result = gateway.ask(question, mode=mode, session_id=session_id)
    return jsonify(result)


@app.route("/stream", methods=["GET"])
def stream():
    question = request.args.get("question", "")
    provider = request.args.get("provider", "claude")
    if not question:
        return jsonify({"error": "No question"}), 400

    stream_proto = gateway.protocols.get("stream")
    if not stream_proto or not stream_proto.available:
        return jsonify({"error": "Streaming not available"}), 503

    def generate():
        yield from stream_proto.stream_sse(question, provider=provider)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/status")
def status():
    return jsonify(gateway.status())


@app.route("/history/<session_id>")
def history(session_id):
    turns = gateway.memory.get(session_id)
    return jsonify([{"role": t.role, "content": t.content, "agent": t.agent} for t in turns])


@app.route("/tools")
def tools():
    return jsonify(gateway.tools.list_tools())


@app.route("/tool/run", methods=["POST"])
def run_tool():
    data = request.json
    tool_name = data.get("tool")
    inp = data.get("input", "")
    result = gateway.tools.run(tool_name, inp)
    return jsonify({"result": result})


@app.route("/.well-known/agent.json")
def agent_card():
    """A2A Agent Card endpoint — makes this gateway discoverable by other A2A agents"""
    a2a = gateway.protocols.get("a2a")
    if a2a:
        import json
        return Response(a2a.get_my_agent_card(), mimetype="application/json")
    return jsonify({"error": "A2A not configured"}), 404


@app.route("/graphql", methods=["POST", "GET"])
def graphql_endpoint():
    """GraphQL endpoint"""
    if request.method == "GET":
        schema = gateway.protocols["graphql"].get_schema()
        return Response(f"<pre>{schema}</pre>", mimetype="text/html")

    data = request.json or {}
    query = data.get("query", "")

    # Simple query router
    if "ask" in query:
        import re
        match = re.search(r'question:\s*"([^"]+)"', query)
        mode_match = re.search(r'mode:\s*"([^"]+)"', query)
        if match:
            question = match.group(1)
            mode = mode_match.group(1) if mode_match else "auto"
            result = gateway.ask(question, mode=mode)
            return jsonify({"data": {"ask": {
                "content": result.get("answer", result.get("final", "")),
                "agent": result.get("agent", ""),
                "taskType": result.get("task_type", "general"),
                "success": result.get("success", True),
                "error": result.get("error")
            }}})

    if "agents" in query:
        s = gateway.status()
        return jsonify({"data": {"agents": s["agents"]}})

    return jsonify({"errors": [{"message": "Query not supported"}]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
