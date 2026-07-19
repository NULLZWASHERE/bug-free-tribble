from http.server import BaseHTTPRequestHandler
import requests
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Block GET requests so browsing to the URL doesn't waste your API key
        self.send_response(405)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Method Not Allowed. Use POST.".encode('utf-8'))

    def do_OPTIONS(self):
        # Handles CORS preflight requests from browsers
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        # 1. Handle CORS and headers right away
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        # 2. Read the incoming request body from the client
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        # Safely parse the JSON body
        try:
            client_payload = json.loads(post_data) if content_length > 0 else {}
        except json.JSONDecodeError:
            client_payload = {}

        text_input = client_payload.get("text", "the text")
        
        # 3. Construct the payload for the NVIDIA API
        # (Moved chat_template_kwargs to the root level because we are not using the openai SDK)
        nvidia_payload = {
            "model": "z-ai/glm-5.2",
            "messages": [{"content": text_input, "role": "user"}],
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 26384,
            "seed": 42,
            "chat_template_kwargs": {
                "enable_thinking": False,
                "clear_thinking": True
            },
            "stream": True
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            # Added 'Bearer ' prefix as required by NVIDIA's strict authorization parser
            "Authorization": "Bearer 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"
        }

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        # 4. Make a streaming request to the NVIDIA API
        with requests.post(url, json=nvidia_payload, headers=headers, stream=True) as r:
            # If NVIDIA returns an error, stream that error back to us
            if r.status_code != 200:
                self.wfile.write(f"Error from NVIDIA API: {r.text}".encode('utf-8'))
                return

            # 5. Stream the chunks directly back to the client
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
