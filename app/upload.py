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

def create_variant():
    variant_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO video_variants (variant_id) VALUES (?)", [variant_id])

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot create video variant: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to create your video. Please try again later.")
    finally:
        db.lock.release()

    return variant_id

def create_video(author, primary_variant):
    video_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute(
            "INSERT INTO videos (video_id, author, created_time, primary_variant) VALUES (?, ?, ?, ?)",
            [
                video_id,
                author,
                time.time(),
                primary_variant
            ]
        )

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

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise UploadError("Sorry, but that file isn't a supported video format.")
            
            os.makedirs("uploads", exist_ok=True)

            variant_id = create_variant()

            create_video(user["uid"], variant_id)

            file.save(pathlib.Path("uploads") / (variant_id + ".upload"))

            return redirect("/", code=302)
        except UploadError as e:
            return render_template(
                "upload/upload.html",
                user=user,
                section="upload",
                allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
                error=str(e)
            )

    return render_template(
        "upload/upload.html",
        user=user,
        section="upload",
        allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
        error=""
    )