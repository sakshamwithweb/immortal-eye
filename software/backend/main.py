from flask import Flask, request
import os
import subprocess

app = Flask(__name__)

upload_at = 'uploads'
os.makedirs(upload_at, exist_ok=True)


@app.route('/upload', methods=['POST'])
def upload():
    clip = request.files['clip']
    webm_file = os.path.join(upload_at, clip.filename)
    mp4_file = os.path.join(upload_at, f"{clip.filename.split('.')[0]}.mp4")
    clip.save(webm_file)

    subprocess.run(
        ["ffmpeg", "-i", webm_file, mp4_file, "-y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    os.remove(webm_file)

    return {'success': True}


if __name__ == '__main__':
    app.run(debug=True, port=5000)
