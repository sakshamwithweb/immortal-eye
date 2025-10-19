from flask import Flask, request
import os
import subprocess
import tempfile
import requests
from twilio.rest import Client
import time
import boto3
from dotenv import load_dotenv

# Config
load_dotenv()
app = Flask(__name__)
headers = {"Authorization": os.getenv("API_KEY")}
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
client = Client(os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"))
s3 = boto3.client(
    "s3",
    endpoint_url="https://hel1.your-objectstorage.com",
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    region_name="eu-central"
)


@app.route('/upload', methods=['POST'])
def upload():
    """
    upload() runs when /upload is called. It takes a video file (clip), converts it to MP4, saves it, uploads it to memories.ai via /serve/api/v1/upload, then polls every 3s to check if the video's parsed.
    """
    # Save file and convert to MP4
    start = time.time()
    clip = request.files['clip']
    webm_file = os.path.join(app.config['UPLOAD_FOLDER'], clip.filename)
    mp4_file = os.path.join(
        app.config['UPLOAD_FOLDER'], f"{clip.filename.split('.')[0]}.mp4")
    clip.save(webm_file)
    subprocess.run(
        ["ffmpeg", "-i", webm_file, mp4_file, "-y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    os.remove(webm_file)

    # Upload to memories.ai
    res1 = requests.post(
        "https://api.memories.ai/serve/api/v1/upload",
        files={
            "file": (os.path.basename(mp4_file), open(mp4_file, 'rb'), "video/mp4")
        },
        data={},
        headers=headers
    )
    endUpload = time.time()
    print(f"Took {endUpload - start:.2f} seconds to upload")

    # Checking whethewr it is parsed or not through polling..
    while True:
        if res1.json()['data']['videoNo']:
            res2 = requests.post("https://api.memories.ai/serve/api/v1/list_videos",
                                 headers=headers, json={"video_no": res1.json()['data']['videoNo']})
            if ((res2.json())["data"]["videos"][0]["status"] == "PARSE"):
                print(res2.json())
                print("Parsed!")
                break
            else:
                print(".")
            time.sleep(3)

    endParse = time.time()
    print(f"Took {endParse - endUpload:.2f} seconds to parse")

    # Detecting abuse
    prompt = f"Hey Memories AI, I have attached a video, look at it and tell me do you see any elder abuse in that means any kind of physical or any other bad abuse that must be informed to their family and caretaker? If yes, Send a strict word 'Yes' or else send 'No' word. No other thing and *No Markdown*"

    req3 = requests.post(
        "https://api.memories.ai/serve/api/v1/chat",
        headers=headers,
        json={
            "video_nos": [res1.json()['data']['videoNo']],
            "prompt": prompt
        },
        stream=False
    )

    endChat = time.time()
    print(f"Took {endChat - endParse:.2f} seconds to detect")

    if "no" in req3.json()["data"]["content"].lower():
        print("No abuse found")
        return {'success': True}

    print("Abuse found, actions will be taken here..")

    receiver_no = "+123456789"  # Dummyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

    # Call
    call = client.calls.create(
        twiml='<Response><Say>Hello Grandpa!</Say></Response>',
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=receiver_no
    )

    # SMS
    # message = client.messages.create(
    #     body="Hey You, are you getting this message? We are from Immortal Eye 👁️",
    #     from_=os.getenv("TWILIO_PHONE_NUMBER"),
    #     to=receiver_no
    # )

    # Save Evidencez
    s3.upload_file(mp4_file, os.getenv("BUCKET_NAME"), f"{clip.filename.split('.')[0]}.mp4", ExtraArgs={'ContentType': 'video/mp4'})
    endSave = time.time()
    print(f"Uploaded evidence, took {endSave - endChat} seconds")


    return {'success': True}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
