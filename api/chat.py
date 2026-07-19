from http.server import BaseHTTPRequestHandler
import requests
import json

# Vercel automatically routes requests to this handler
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Read the incoming request body from the client
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        # If the client sent a message body, parse it. Otherwise, default to empty.
        try:
            client_payload = json.loads(post_data) if post_length > 0 else {}
        except json.JSONDecodeError:
            client_payload = {}

        # The client can optionally override the text, model, etc., 
        # but we default to your provided configuration.
        text_input = client_payload.get("text", "the text")
        
        # 2. Construct the payload for the NVIDIA API
        nvidia_payload = {
            "model": "z-ai/glm-5.2",
            "messages": [{"content": text_input, "role": "user"}],
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 16384,
            "seed": 42,
            "extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": False,
                    "clear_thinking": True
                }
            },
            "stream": True
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": "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"
        }

        # 3. Make a streaming request to the NVIDIA API
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        # Stream=True keeps the connection open and downloads chunks as they arrive
        with requests.post(url, json=nvidia_payload, headers=headers, stream=True) as r:
            if r.status_code != 200:
                # Forward the error back to the client if it failed
                self.send_response(r.status_code)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(r.text.encode('utf-8'))
                return

            # 4. Send a 200 response to the client and prepare for streaming
            self.send_response(200)
            self.send_header("Content-type", "text/plain") # Or application/x-ndjson if you prefer pure JSON chunks
            self.end_headers()

            # 5. Stream the chunks directly back to the client
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    # Depending on how you want the client to receive this, 
                    # you can format the chunk here. 
                    # We'll just forward the raw Server-Sent Event (SSE) strings.
                    self.wfile.write(chunk)
                    
    # Required to handle CORS if you are calling this from a browser frontend
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        
    def do_POST(self): # Duplicate method to inject CORS headers into POST
        self.send_header("Access-Control-Allow-Origin", "*")
        self.do_POST_impl()

    def do_POST_impl(self): # Moved the main logic here to inject CORS headers
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            client_payload = json.loads(post_data) if content_length > 0 else {}
        except json.JSONDecodeError:
            client_payload = {}

        text_input = client_payload.get("text", "the text")
        
        nvidia_payload = {
            "model": "z-ai/glm-5.2",
            "messages": [{"content": text_input, "role": "user"}],
            "temperature": 1,
            "top_p": 1,
            "max_tokens": 16384,
            "seed": 42,
            "extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": False,
                    "clear_thinking": True
                }
            },
            "stream": True
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": "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"
        }

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        
        with requests.post(url, json=nvidia_payload, headers=headers, stream=True) as r:
            if r.status_code != 200:
                self.send_response(r.status_code)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(r.text.encode('utf-8'))
                return

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
