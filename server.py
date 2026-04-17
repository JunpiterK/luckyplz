import os
import socket
from flask import Flask, send_from_directory, send_file

app = Flask(__name__)

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')

@app.route('/')
def index():
    return send_file(os.path.join(PUBLIC, 'index.html'))

@app.route('/<path:path>')
def static_files(path):
    full = os.path.join(PUBLIC, path)
    # Directory -> serve index.html inside it
    if os.path.isdir(full):
        idx = os.path.join(full, 'index.html')
        if os.path.isfile(idx):
            return send_file(idx)
    # Regular file
    if os.path.isfile(full):
        return send_from_directory(PUBLIC, path)
    return 'Not Found', 404

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    local_ip = get_local_ip()

    print('=' * 56)
    print('  NotMePlz Game Server')
    print('=' * 56)
    print(f'  Local:    http://localhost:{port}')
    print(f'  Network:  http://{local_ip}:{port}')
    print('-' * 56)
    print('  Same Wi-Fi/LAN users can access via the Network URL')
    print('  For external access, use port forwarding or ngrok')
    print('=' * 56)

    app.run(host=host, port=port, debug=False)
