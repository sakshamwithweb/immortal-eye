import os
import subprocess


def file_save(upload_dir, clip):
    """Takes upload_dir and clip file, save it, convert to mp4 and delete waste file. Returns mp4_file path"""
    webm_file = os.path.join(upload_dir, clip.filename)
    mp4_file = os.path.join(upload_dir, f"{clip.filename.split('.')[0]}.mp4")
    clip.save(webm_file)
    subprocess.run(
        ["ffmpeg", "-i", webm_file, mp4_file, "-y"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    os.remove(webm_file)

    return mp4_file
