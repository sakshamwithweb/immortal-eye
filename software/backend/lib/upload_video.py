import requests
import os

# In future, confirm the output


def upload_video(mp4_file, headers):
    """Takes mp4_file and headers then upload the video in memories.ai"""
    res1 = requests.post(
        "https://api.memories.ai/serve/api/v1/upload",
        files={
            "file": (os.path.basename(mp4_file), open(mp4_file, 'rb'), "video/mp4")
        },
        data={},
        headers=headers
    )
    return res1