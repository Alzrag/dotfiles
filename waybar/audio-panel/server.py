#!/usr/bin/env python3
from flask import Flask, jsonify
import subprocess

app = Flask(__name__)

def get_audio_status():
    # Default device
    out = subprocess.run(['wpctl', 'status'], capture_output=True, text=True).stdout
    default = ""
    for line in out.splitlines():
        if '*' in line and 'Sink' not in line:
            default = line.split()[-1]  # crude, improve parsing
            break
    return {"default_device": default, "streams": []}

@app.route("/api/audio")
def api_audio():
    return jsonify(get_audio_status())

app.run(port=9000)

