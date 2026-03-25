"""
Minimal HTTP health check server for Celery worker.
Railway requires an HTTP healthcheck endpoint. Celery doesn't serve HTTP,
so this tiny server runs alongside Celery to respond to healthchecks.
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/v1/health/" or self.path == "/health/" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"kibray-worker"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence access logs to avoid noise
        pass


def start_health_server():
    port = int(os.getenv("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"✅ Worker healthcheck server listening on port {port}")
    server.serve_forever()


def run_in_background():
    """Start the health server in a background daemon thread."""
    thread = threading.Thread(target=start_health_server, daemon=True)
    thread.start()


if __name__ == "__main__":
    start_health_server()
