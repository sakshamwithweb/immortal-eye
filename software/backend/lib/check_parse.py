import requests
import time


def check_parse(video_no, headers):
    """Takes video_no and headers, check parse status through polling the memories.ai api"""
    while True:
        if video_no:
            res2 = requests.post("https://api.memories.ai/serve/api/v1/list_videos",
                                 headers=headers, json={"video_no": video_no})
            if ((res2.json())["data"]["videos"][0]["status"] == "PARSE"):
                print("Parsed!")
                break
            else:
                print(".")
            time.sleep(3)
