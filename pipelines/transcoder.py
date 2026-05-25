import logging
import subprocess
import pathlib
import os
import ffmpeg
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
    video_id = upload["video_id"]
    variant_id = upload["variant_id"]
    video_dir = pathlib.Path("videos") / video_id / "variants" / variant_id

    update_transcoder_status(variant_id, 1)

    os.makedirs(video_dir, exist_ok=True)

    try:
        upload_path = str(pathlib.Path("uploads") / (variant_id + ".upload"))

        probe = ffmpeg.probe(upload_path)
        width = None
        height = None

        for stream in probe["streams"]:
            if stream["codec_type"] == "video":
                width = stream["width"]
                height = stream["height"]

                break

        if width is None or height is None:
            raise Exception("Could not find a valid video stream")

        new_width = width * 240 // height

        subprocess.call([
            "ffmpeg",
            "-i", upload_path,
            "-c:v", "libx264",
            "-crf", "28",
            "-preset", "ultrafast",
            "-threads", "0",
            "-s", f"{new_width}x240",
            "-f", "dash",
            str(video_dir / "video.mpd")
        ])

        update_transcoder_status(variant_id, 2)
    except Exception as e:
        logger.error("Transcoding error when invoking ffmpeg: %s", repr(e))

        update_transcoder_status(variant_id, -1)

def run():
    logger.info("Checking transcoder queue...")

    data = common.fetch_private_api("/privateapi/uploadqueue")

    if len(data["variants"]) > 0:
        transcode(data["variants"][0])