"""Run: python server.py  →  http://localhost:8080"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

def load_env():
    p = Path('.env')
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
KEY = os.environ.get('OPENROUTER_API_KEY', '')

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            html = Path('index.html').read_text('utf-8')
            html = html.replace('</head>', f'\n<script>window.OPENROUTER_API_KEY="{KEY}";</script>\n</head>', 1)
            body = html.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        if self.path == '/api/chat':
            import api.chat
            handler = api.chat.handler(self.request, self.client_address, self.server)
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        if self.path == '/api/chat':
            import api.chat
            handler = api.chat.handler(self.request, self.client_address, self.server)
        else:
            self.send_response(200); self.end_headers()

    def log_message(self, f, *a): print(f"  {a[0]} {a[1]}")

if __name__ == '__main__':
    print(f"\n🚀  http://localhost:8080")
    print(f"   {'✅ API Key loaded' if KEY and KEY.lower() != 'your_key_here' else '⚠️  Add key to .env first'}\n")
    HTTPServer(('', 8080), H).serve_forever()
