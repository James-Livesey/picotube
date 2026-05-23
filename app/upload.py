import logging
import os
import pathlib
import time
from flask import Blueprint, request, render_template, redirect

import common
import db
from auth import get_current_user

upload = Blueprint("upload", __name__)
logger = logging.getLogger()

ALLOWED_MIME_TYPES = ["video/mp4", "video/x-matroska", "video/webm", "video/x-msvideo", "video/quicktime"]

class UploadError(Exception):
    pass

def create_variant(video):
    variant_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO video_variants (variant_id, video) VALUES (?, ?)", [variant_id, video])

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot create video variant: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to create your video. Please try again later.")
    finally:
        db.lock.release()

    return variant_id

def create_subtitles(video, type, subtitles):
    subtitles_id = common.generate_key()

    try:
        subtitles_dir = pathlib.Path("videos") / video / "subtitles"

        os.makedirs(subtitles_dir, exist_ok=True)

        file = open(subtitles_dir / (subtitles_id + ".vtt"), "w")

        file.write(subtitles)
        file.close()

        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO video_subtitles (subtitles_id, video, type) VALUES (?, ?, ?)", [subtitles_id, video, type])

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot create video subtitles: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to create your video. Please try again later.")
    finally:
        db.lock.release()

def create_video(author):
    video_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO videos (video_id, author, created_time) VALUES (?, ?, ?)", [video_id, author, time.time()])

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot create video: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to create your video. Please try again later.")
    finally:
        db.lock.release()

    return video_id

@upload.route("/upload", methods=["GET", "POST"])
def upload_area():
    user = get_current_user(request)

    if user is None:
        return redirect("/signin?go=/upload", code=302)

    if request.method == "POST":
        try:
            if "file" not in request.files or request.files["file"].filename == "":
                raise UploadError("Please actually upload something.")

            file = request.files["file"]
            subtitles = request.form.get("subtitles") or ""

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise UploadError("Sorry, but that file isn't a supported video format.")

            os.makedirs("uploads", exist_ok=True)

            video_id = create_video(user["uid"])
            variant_id = create_variant(video_id)

            if subtitles != "":
                create_subtitles(video_id, "generated", subtitles)

            file.save(pathlib.Path("uploads") / (variant_id + ".upload"))

            return redirect("/", code=302)
        except UploadError as e:
            return render_template(
                "upload/upload.html",
                user=user,
                section="upload",
                allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
                error=str(e)
            ), 400

    return render_template(
        "upload/upload.html",
        user=user,
        section="upload",
        allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
        error=""
    )