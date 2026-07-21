from __future__ import annotations

import os

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/home', methods=['GET'])
def home():
    server_id = os.environ.get('SERVER_ID', 'Unknown')
    return jsonify({
        "message": f"Hello from Server: {server_id}",
        "status": "successful"
    }), 200


@app.route('/echo', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def echo():
    return jsonify({
        "method": request.method,
        "path": request.path,
        "data": request.get_data(as_text=True),
        "status": "successful"
    }), 200


@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
