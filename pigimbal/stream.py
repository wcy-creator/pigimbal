"""
MJPEG + JSON API web server for live camera feed + gimbal control.
"""
import time
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from .camera import Camera
except ImportError:
    from camera import Camera


class StreamHandler(BaseHTTPRequestHandler):
    camera = None
    gimbal = None

    def do_GET(self):
        if self.path == '/':
            self._serve_index()
        elif self.path == '/snapshot':
            self._serve_snapshot()
        elif self.path == '/status':
            self._serve_json({"status": "ok"})
        elif self.path.startswith('/move'):
            self._handle_move()
        elif self.path.startswith('/mjpeg'):
            self._serve_mjpeg()
        else:
            self.send_error(404)

    def _serve_index(self):
        html = """<!DOCTYPE html><html><head><title>PiGimbal</title>
        <style>body{background:#1a1a2e;color:#eee;font-family:monospace;text-align:center;padding:40px}
        h1{color:#00d4ff}img{border:2px solid #333;border-radius:8px;max-width:640px}
        button{padding:10px 20px;margin:5px;background:#00d4ff;border:none;border-radius:5px;
        font-size:16px;cursor:pointer;color:#1a1a2e}button:hover{background:#00ff88}
        #status{color:#00ff88;margin-top:20px}</style></head><body>
        <h1>PiGimbal Live</h1>
        <img id="feed" src="/mjpeg" width="640">
        <div style="margin-top:20px">
        <button onclick="move(-10,0)">Pan Left</button>
        <button onclick="move(0,0)">Center</button>
        <button onclick="move(10,0)">Pan Right</button>
        <br>
        <button onclick="move(0,-10)">Tilt Up</button>
        <button onclick="move(0,10)">Tilt Down</button>
        </div>
        <div id="status">Loading...</div>
        <script>
        function move(p,t){fetch('/move?pan='+p+'&tilt='+t).then(r=>r.json()).then(d=>{document.getElementById('status').innerText=JSON.stringify(d)})}
        setInterval(()=>{fetch('/status').then(r=>r.json()).then(d=>{document.getElementById('status').innerText='Pan:'+d.pan+' Tilt:'+d.tilt+' Track:'+(d.tracking?'ON':'OFF')})},1000);
        </script></body></html>"""
        self._respond(200, 'text/html', html.encode())

    def _serve_snapshot(self):
        if self.camera:
            frame = self.camera.read()
            if frame is not None:
                import cv2
                _, jpg = cv2.imencode('.jpg', frame)
                self._respond(200, 'image/jpeg', jpg.tobytes())
                return
        self.send_error(503)

    def _serve_mjpeg(self):
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        import cv2
        try:
            while True:
                if self.camera:
                    frame = self.camera.read()
                    if frame is not None:
                        _, jpg = cv2.imencode('.jpg', frame)
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n')
                        self.wfile.write(jpg.tobytes())
                        self.wfile.write(b'\r\n')
                time.sleep(0.033)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _handle_move(self):
        params = {}
        if '?' in self.path:
            for pair in self.path.split('?')[1].split('&'):
                k, v = pair.split('=')
                params[k] = float(v)
        if self.gimbal:
            self.gimbal.nudge(params.get('pan', 0), params.get('tilt', 0))
        pan, tilt = self.gimbal.query() if self.gimbal else (0, 0)
        self._serve_json({"pan": round(pan, 1), "tilt": round(tilt, 1)})

    def _serve_json(self, data):
        self._respond(200, 'application/json', json.dumps(data).encode())

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress logs


def serve(camera=None, gimbal=None, port=8080):
    """Start web server."""
    StreamHandler.camera = camera
    StreamHandler.gimbal = gimbal
    server = HTTPServer(('0.0.0.0', port), StreamHandler)
    print("[Stream] http://0.0.0.0:%d" % port)
    server.serve_forever()
