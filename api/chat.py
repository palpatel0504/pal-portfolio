import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-3-haiku"


def _send_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def handle_request(handler):
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key or api_key.lower() == "your_key_here":
        _send_json(handler, 500, {"error": {"message": "Missing OPENROUTER_API_KEY environment variable."}})
        return

    try:
        incoming = _read_json(handler)
        messages = incoming.get("messages", [])
        if not messages:
            _send_json(handler, 400, {"error": {"message": "Request must include messages."}})
            return

        payload = {
            "model": incoming.get("model") or DEFAULT_MODEL,
            "messages": messages,
            "temperature": incoming.get("temperature", 0.7),
            "max_tokens": incoming.get("max_tokens", 500),
        }
        request = Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": handler.headers.get("Origin", "http://localhost:8080"),
                "X-Title": "Pal Patel Portfolio",
            },
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        _send_json(handler, 200, result)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        _send_json(handler, exc.code, {"error": {"message": detail or str(exc)}})
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        _send_json(handler, 500, {"error": {"message": str(exc)}})


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        handle_request(self)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
