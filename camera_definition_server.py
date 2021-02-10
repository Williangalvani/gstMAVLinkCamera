from flask import Flask, send_file
import threading

app = Flask(__name__)
@app.route('/')

def hello_world():
    return send_file("camera_definitions/example.xml", mimetype='text/plain')

class CameraDefinitionServer(threading.Thread):

    def __init__(self, device, port):
        super().__init__()
        self.port = port

    def run(self):
        app.run(host='0.0.0.0', port=self.port, debug=False)