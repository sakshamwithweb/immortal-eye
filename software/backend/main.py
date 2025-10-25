from flask import Flask, request
import os
import subprocess
import tempfile
import requests
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Start
import time
import boto3
from dotenv import load_dotenv
import json
from concurrent.futures import ThreadPoolExecutor
from united_states import UnitedStates
import urllib

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
    upload() runs when /upload is called. It takes a video file (clip), converts it to MP4, saves it, uploads it to memories.ai via /serve/api/v1/upload, then polls every 3s to check if the video's parsed. Afterwards, it uses /api/v1/chat to detect alder abuse and if it detects any abuse, it takes action immediately like calling to local APS and caretakers, sending sms in case they don't attend using twillio API and it also preserve the evidence video in our storage bucket.
    """
    # Save file and convert to MP4
    start = time.time()
    clip = request.files['clip']
    caretakers_number = json.loads(request.form.get('numbers'))["caretakers"]
    location = json.loads(request.form.get('location'))

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

    # Call
    def make_call(number):
        call = client.calls.create(
            twiml='<Response><Say>Hello Grandpa!</Say></Response>',
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=number
        )
        return call
        
    with ThreadPoolExecutor(max_workers=10) as executor: # Call to 10 numbers at once parallelly
        executor.map(make_call, caretakers_number)

    # Function to get US state form coords
    def get_state_from_coords(latitude, longitude):
        us = UnitedStates()
        state = us.from_coords(latitude, longitude)
        return state[0].name if state else None
    
    # Get nearest APS and Call
    aps_data = []
    with open("data/aps.json","r") as file:
        aps_data = json.loads(file.read())

    state_name = get_state_from_coords(location.latitude, location.longitude)
    aps_number = (next((state for state in aps_data if state["State"] == state_name), None)).get("aps_no") # Got APS Number
    user_data = json.dumps({"location":location}) # Need more, like name, accurate place name etc etc. to give to cops
    user_data_query_string = urllib.parse.quote(user_data)

    response = VoiceResponse()
    start = Start()
    start.transcription(
        status_callback_url=f'{os.getenv('SERVER_URL')}/transcript?user_data={user_data_query_string}', # Your callback url
        track='inbound_track'
    )
    response.append(start)
    response.pause(30) # To keep it alive or else it wil just follow things then close

    call = client.calls.create(
        twiml=str(response),
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=aps_number
    )
    print(call.sid)    

    # SMS
    def send_sms(number):
        sms = client.messages.create(
            body="Hey You, are you getting this message? We are from Immortal Eye 👁️",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=number
        )
        return sms
        
    with ThreadPoolExecutor(max_workers=10) as executor: # Send sms to everyone parallelly
        executor.map(send_sms, caretakers_number)

    # Save Evidence
    s3.upload_file(mp4_file, os.getenv("BUCKET_NAME"), f"{clip.filename.split('.')[0]}.mp4", ExtraArgs={'ContentType': 'video/mp4'})
    endSave = time.time()
    print(f"Uploaded evidence, took {endSave - endChat} seconds")


    return {'success': True}















context = []

def detect_action(transcript, context, given_data):
    """
    AI core: Takes the latest transcript, detects if it's IVR or human,
    and returns TwiML snippet (without <Response>) for the next action. 
    Ultimate goal is to talk to a human and give all the infos..
    """

    prompt = f"""
You are a real-time AI call assistant integrated with Twilio.

Your mission:
- If the other side is an **IVR or bot**, do everything possible to quickly reach a **live human agent**.
  - You can press digits (<Play digits="1"/>, <Play digits="0"/>, etc.),
  - say words (<Say>Representative</Say>, <Say>Operator</Say>, etc.),
  - or wait briefly (<Pause length="3"/>).
  - Be creative and efficient — your goal is to reach a human quickly.
- If the other side is a **human**, respond naturally using the data provided in "given_data", 
  and then communicate this message clearly:
  "There is a grandma in the location I have shared, she is abused by her caretakers."

If the other side sounds like a live person (they introduce themselves or say 'how may I help you'), 
treat them as HUMAN immediately and deliver the message using the given data.

You must return only valid **TwiML command(s)** (e.g., <Say>...</Say>, <Play digits="1"/>, <Pause length="3"/>, <Hangup/>).
Do not include <Response> wrapper, any JSON or Markdown — only the inner TwiML.

Here is the full conversational context so far:
{context}

Here is the user-provided data you can use if asked for information (e.g. name, location, etc.):
{given_data}

Here is the most recent transcript from the call:
"{transcript}"

Be fast, natural, and adaptive. Respond with only TwiML that should be appended next.
"""

    print(prompt)

    # call the API
    resp = requests.post("https://api.openai.com/v1/chat/completions",
                         json={
                             "model": "gpt-4o-mini",
                             "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": 100,
                             "temperature": 0
                         },
                         headers={"Authorization": f"Bearer {os.getenv("OPENAI_API_KEY")}"})
    data = resp.json()
    twiml_snippet = data["choices"][0]["message"]["content"].strip()
    print("AI TwiML:", twiml_snippet)
    code = f"{twiml_snippet} <Pause length='30'/>"
    return code

def update_call_with_twiml(call_sid, twiml):
    return client.calls(call_sid).update(twiml=f"<Response>{twiml}</Response>")


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
        transcript = json.loads(payload.get(
            'TranscriptionData')).get('transcript')

        # Detect what actions to take based on transcription and user data.
        ai_action = detect_action(transcript, context, user_data)

        # Update call
        update_call_with_twiml(call_sid, ai_action)

        # Save the transcription and response in context
        context.append({"opponent": transcript, "action_taken": ai_action})

    elif "stop" in payload.get("TranscriptionEvent"):
        context = []
        print("Stopped")

    return {'success': True}
