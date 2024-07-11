from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import threading
import pyautogui
import numpy as np
import base64
from PIL import Image
import io
import random
import cv2  # Make sure OpenCV is installed as `opencv-python`

app = Flask(__name__)
socketio = SocketIO(app)

# In-memory storage for sharing codes and streams
streams = {}

def generate_code():
    return f"{random.randint(100000, 999999)}"

@app.route('/share', methods=['POST'])
def share():
    code = generate_code()
    streams[code] = {'status': 'sharing'}
    return jsonify({'status': 'success', 'code': code})

@app.route('/start-sharing/<code>', methods=['POST'])
def start_sharing(code):
    if code in streams:
        streams[code]['status'] = 'active'
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

def capture_screen():
    while True:
        for code, stream in streams.items():
            if stream['status'] == 'active':
                # Capture the screen
                screenshot = pyautogui.screenshot()
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                # Convert image to bytes and then to base64
                _, buffer = cv2.imencode('.jpg', img)
                img_bytes = buffer.tobytes()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                # Emit the image to the client
                socketio.emit('screen_update', {'code': code, 'data': img_base64})

        # Adjust the sleep interval as needed
        socketio.sleep(1)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    threading.Thread(target=capture_screen, daemon=True).start()
    socketio.run(app, debug=True)
