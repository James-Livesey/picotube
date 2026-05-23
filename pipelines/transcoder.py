import logging
import subprocess
import pathlib
import os
from pipelines import common

logger = logging.getLogger(name="transcoder")

def update_transcoder_status(variant_id, status):
    common.fetch_private_api(
        "/privateapi/uploadqueue/" + variant_id,
        method="PUT",
        body={
            "transcoder_status": status
        }
    )

def transcode(upload):
    variant_id = upload["variant_id"]
    video_dir = pathlib.Path("videos") / variant_id

    update_transcoder_status(variant_id, 1)

    os.makedirs(video_dir, exist_ok=True)

    try:
        subprocess.call([
            "ffmpeg",
            "-re",
            "-i", str(pathlib.Path("uploads") / (variant_id + ".upload")),
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "ultrafast",
            "-threads", "0",
            "-s", "320x240",
            "-f", "dash",
            str(video_dir / "video.mpd")
        ])

        update_transcoder_status(variant_id, 2)
    except Exception as e:
        logger.error("Transcoding error when invoking ffmpeg: %s", repr(e))

        update_transcoder_status(variant_id, -1)

def run():
    data = common.fetch_private_api("/privateapi/uploadqueue")

    logger.info(data)

    if len(data["variants"]) > 0:
        transcode(data["variants"][0])