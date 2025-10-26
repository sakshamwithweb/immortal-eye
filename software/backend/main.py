from flask import Flask, request
import os
import tempfile
import requests
from twilio.rest import Client
from dotenv import load_dotenv
import json
import urllib

from lib.file_save import file_save
from lib.upload_video import upload_video
from lib.check_parse import check_parse
from lib.detect_abuse import detect_abuse
from lib.actions import call_to_caretakers, sms_to_caretakers, call_to_aps
from lib.actions_lib.save_evidence import save_evidence
from lib.aps_call_transcript.choose_action import choose_action
from lib.aps_call_transcript.update_call_with_twiml import update_call_with_twiml

# Config
load_dotenv()
app = Flask(__name__)
headers = {"Authorization": os.getenv("API_KEY")}
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

@app.route('/upload', methods=['POST'])
def upload():
    """
    upload() runs when /upload is called. It takes a video file (clip), converts it to MP4, saves it, uploads it to memories.ai via /serve/api/v1/upload, then polls every 3s to check if the video's parsed. Afterwards, it uses /api/v1/chat to detect alder abuse and if it detects any abuse, it takes action immediately like calling to local APS and caretakers, sending sms in case they don't attend using twillio API and it also preserve the evidence video in our storage bucket.
    """
    clip = request.files['clip']
    caretakers_number = json.loads(request.form.get('numbers'))["caretakers"]
    location = json.loads(request.form.get('location'))


    # Save file and convert to MP4
    mp4_file = file_save(app.config['UPLOAD_FOLDER'], clip)

    # Upload to memories.ai
    res1 = upload_video(mp4_file, headers)
    video_no = res1.json()['data']['videoNo']

    # Checking whether it is parsed or not
    check_parse(video_no, headers)

    # Detecting abuse
    abuse = detect_abuse(video_no, headers)

    if abuse['abuse'] == False:
        print("No abuse found")
        return {'success': True}

    print("Abuse found, actions will be taken parallelly here..")

    # Call to Caretakers
    call_to_caretakers(client, os.getenv("TWILIO_PHONE_NUMBER"), caretakers_number)

    # Sms to Caretakers
    sms_to_caretakers(client, os.getenv("TWILIO_PHONE_NUMBER"), caretakers_number)

    # Call to APS
    sid = call_to_aps(location, os.getenv("SERVER_URL"), client, os.getenv("TWILIO_PHONE_NUMBER"))

    # Save Evidence
    save_evidence(mp4_file, os.getenv("BUCKET_NAME"), clip, os.getenv("S3_ACCESS_KEY"), os.getenv("S3_SECRET_KEY"), os.getenv("S3_REGION"), os.getenv("S3_ENDPOINT"))

    return {'success': True}


context = []
@app.route('/transcript', methods=['POST'])
def transcript():
    global context
    payload = request.form
    call_sid = payload.get("CallSid")
    user_data_encoded = request.args.get("user_data")
    if user_data_encoded:
        # It will be data about user like name, address, number, video etc that will need during talk
        user_data = json.loads(urllib.parse.unquote(user_data_encoded))
    else:
        user_data = {}

    if "started" in payload.get("TranscriptionEvent"):
        print("Started")
    elif "content" in payload.get("TranscriptionEvent"):
        transcript = json.loads(payload.get('TranscriptionData')).get('transcript')

        # Detect what actions to take based on transcription and user data.
        ai_action = choose_action(transcript, context, user_data, os.getenv("OPENAI_API_KEY"))

        # Update call action
        update_call_with_twiml(call_sid, ai_action, client)

        # Save the transcription and response in context
        context.append({"opponent": transcript, "action_taken": ai_action})

    elif "stop" in payload.get("TranscriptionEvent"):
        context = []
        print("Stopped")

    return {'success': True}
