import os
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# Simple function to load .env manually
def load_env():
    env = {}
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
    return env

env = load_env()
TELEGRAM_BOT_TOKEN = env.get('TELEGRAM_BOT_TOKEN', os.environ.get('TELEGRAM_BOT_TOKEN'))
TELEGRAM_CHAT_ID = env.get('TELEGRAM_CHAT_ID', os.environ.get('TELEGRAM_CHAT_ID'))
PORT = int(env.get('PORT', os.environ.get('PORT', 5000)))

class ContactHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/contact':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid JSON payload'}).encode('utf-8'))
                return

            name = data.get('name')
            email = data.get('email')
            message = data.get('message')

            if not name or not email or not message:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing name, email, or message'}).encode('utf-8'))
                return

            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Telegram configuration missing on server'}).encode('utf-8'))
                return

            # Format Telegram Message
            text_message = f"📩 *New Contact Message*\n\n👤 *Name:* {name}\n✉️ *Email:* {email}\n📝 *Message:*\n{message}"

            # Prepare Request to Telegram
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': text_message,
                'parse_mode': 'Markdown'
            }
            req_data = json.dumps(payload).encode('utf-8')

            try:
                req = urllib.request.Request(
                    telegram_url, 
                    data=req_data, 
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req) as response:
                    res_body = response.read().decode('utf-8')
                    res_data = json.loads(res_body)
                    
                    if res_data.get('ok'):
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True, 'message': 'Message sent successfully'}).encode('utf-8'))
                    else:
                        self.send_response(502)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'Telegram returned an error', 'details': res_data}).encode('utf-8'))
            except Exception as e:
                print("Error sending message to Telegram:", e)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to communicate with Telegram API', 'details': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=ContactHandler, port=PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting contact server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
