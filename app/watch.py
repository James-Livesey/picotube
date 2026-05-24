import logging
import pathlib
from flask import Blueprint, request, render_template, send_from_directory

from auth import get_current_user

watch = Blueprint("watch", __name__)
logger = logging.getLogger()

@watch.route("/watch/<video_id>")
def watch_video(video_id):
    return render_template(
        "watch/watch.html",
        user=get_current_user(request),
        section="watch",
        video_id=video_id
    )

@watch.route("/watch/<video_id>/<path:path>")
def watch_file(video_id, path):
    print(video_id, pathlib.Path(video_id) / path)
    return send_from_directory(pathlib.Path("..") / "videos", pathlib.Path(video_id) / path)