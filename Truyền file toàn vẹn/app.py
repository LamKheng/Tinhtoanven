from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, join_room, emit
import os
import hashlib

app = Flask(__name__)
socketio = SocketIO(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', f'Joined room: {room}', to=room)

@socketio.on('send_file')
def on_send_file(data):
    room = data['room']
    filename = data['filename']
    filedata = data['filedata'].encode('latin1')  # Binary
    client_hash = data['filehash']

    # Lưu file
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(filedata)

    # Server tính lại SHA-256
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    server_hash = sha256.hexdigest()

    if server_hash == client_hash:
        emit('file_result', {
            'status': 'ok',
            'message': 'File received & verified!',
            'download_link': f'/download/{filename}',
            'filehash': server_hash
        }, to=room)
    else:
        emit('file_result', {
            'status': 'error',
            'message': 'Hash mismatch! File corrupted.'
        }, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
