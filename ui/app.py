import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template
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
    if not question:
        return jsonify({"error": "No question provided"}), 400
    result = gateway.ask(question, mode=mode)
    return jsonify(result)


@app.route("/status")
def status():
    return jsonify(gateway.status())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
