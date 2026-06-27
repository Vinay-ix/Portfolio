import os
import json
import urllib.request
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler


# ----------------------------
# Load .env
# ----------------------------
def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


env = load_env()

TELEGRAM_BOT_TOKEN = env.get(
    "TELEGRAM_BOT_TOKEN",
    os.environ.get("TELEGRAM_BOT_TOKEN")
)

TELEGRAM_CHAT_ID = env.get(
    "TELEGRAM_CHAT_ID",
    os.environ.get("TELEGRAM_CHAT_ID")
)

PORT = int(os.environ.get("PORT", env.get("PORT", 5000)))


class PortfolioHandler(BaseHTTPRequestHandler):

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # ----------------------------
    # Serve Website Files
    # ----------------------------
    def do_GET(self):

        if self.path == "/":
            filepath = "index.html"
        else:
            filepath = self.path.lstrip("/")

        if os.path.isfile(filepath):

            content_type = (
                mimetypes.guess_type(filepath)[0]
                or "application/octet-stream"
            )

            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()

            with open(filepath, "rb") as f:
                self.wfile.write(f.read())

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    # ----------------------------
    # Contact API
    # ----------------------------
    def do_POST(self):

        if self.path != "/api/contact":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)

        try:
            data = json.loads(body.decode())
        except:
            self.send_response(400)
            self.end_headers()
            return

        name = data.get("name")
        email = data.get("email")
        message = data.get("message")

        if not all([name, email, message]):
            self.send_response(400)
            self.end_headers()
            return

        text = (
            "📩 *New Portfolio Contact*\n\n"
            f"👤 Name: {name}\n"
            f"📧 Email: {email}\n\n"
            f"💬 {message}"
        )

        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }).encode()

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            urllib.request.urlopen(req)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps({
                "success": True
            }).encode())

        except Exception as e:

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }).encode())


if __name__ == "__main__":
    print(f"Running on port {PORT}")
    server = HTTPServer(("", PORT), PortfolioHandler)
    server.serve_forever()
