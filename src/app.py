"""
TrailPacer AI - Web Application Server
Serves static UI and REST endpoints for local inference and workout pacing.
"""

import json
import logging
import mimetypes
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import generate_workout, load_fallback_workout, MODEL_NAME, OLLAMA_URL
from src.validator import load_schema

STATIC_DIR = Path(__file__).resolve().parent / "static"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrailPacerWeb")


class TrailPacerHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            import requests
            ollama_online = False
            try:
                r = requests.get(OLLAMA_URL.replace("/api/generate", "/api/tags"), timeout=2)
                ollama_online = r.status_code == 200
            except Exception:
                ollama_online = False

            return self.send_json(200, {
                "status": "online",
                "model": MODEL_NAME,
                "ollama_connected": ollama_online,
                "endpoint": OLLAMA_URL
            })

        if path == "/api/schema":
            schema = load_schema()
            return self.send_json(200, schema)

        # Static file serving
        if path == "/" or path == "":
            file_path = STATIC_DIR / "index.html"
        else:
            rel_path = path.lstrip("/")
            file_path = STATIC_DIR / rel_path

        if file_path.exists() and file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "text/plain"

            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, f"File not found: {path}")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/generate":
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len == 0:
                return self.send_json(400, {"error": "Missing JSON request body"})

            body_str = self.rfile.read(content_len).decode("utf-8")
            try:
                payload = json.loads(body_str)
            except json.JSONDecodeError:
                return self.send_json(400, {"error": "Invalid JSON format"})

            activity = payload.get("activity", "fartlek_run")
            duration = int(payload.get("duration", 30))
            fitness_level = payload.get("fitness_level", "intermediate")

            start_t = time.time()
            try:
                workout = generate_workout(
                    activity=activity,
                    duration=duration,
                    fitness_level=fitness_level,
                    max_retries=1,
                    use_fallback_on_error=True
                )
                latency = round(time.time() - start_t, 2)
                return self.send_json(200, {
                    "success": True,
                    "workout": workout,
                    "latency_seconds": latency,
                    "model_used": MODEL_NAME
                })
            except Exception as e:
                logger.exception("Failed generation:")
                return self.send_json(500, {
                    "success": False,
                    "error": str(e)
                })

        self.send_error(404, f"Endpoint not found: {parsed.path}")

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} - {args[1]}\n")


def run_server(port: int = 8000, host: str = "0.0.0.0"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, TrailPacerHandler)
    logger.info("TrailPacer AI Web UI running at http://localhost:%d", port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server terminated by user.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port=port)
