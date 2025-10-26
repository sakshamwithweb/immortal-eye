import requests


def detect_abuse(video_no, headers):
    """takes video_no and headers, checks for any abuse and return a dict like: {'abuse':True/False}"""
    prompt = f"Hey Memories AI, I have attached a video, look at it and tell me do you see any elder abuse in that means any kind of physical or any other bad abuse that must be informed to their family and caretaker? If yes, Send a strict word 'Yes' or else send 'No' word. No other thing and *No Markdown*"

    req3 = requests.post(
        "https://api.memories.ai/serve/api/v1/chat",
        headers=headers,
        json={
            "video_nos": [video_no],
            "prompt": prompt
        },
        stream=False
    )

    return {'abuse': ("yes" in req3.json()["data"]["content"].lower())}