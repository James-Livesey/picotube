import logging
import os
import pathlib
from flask import Blueprint, request, render_template, redirect

import common
import db
from auth import get_current_user

upload = Blueprint("upload", __name__)
logger = logging.getLogger()

ALLOWED_MIME_TYPES = ["video/mp4", "video/x-matroska", "video/webm", "video/x-msvideo", "video/quicktime"]

class UploadError(Exception):
    pass

@upload.route("/upload", methods=["GET", "POST"])
def upload_area():
    if get_current_user(request) is None:
        return redirect("/signin?go=/upload", code=302)

    if request.method == "POST":
        try:
            print(request.data, request.stream, request.files, request.form)
            print(request.files.get("file"))
            if "file" not in request.files or request.files["file"].filename == "":
                raise UploadError("Please actually upload something.")

            file = request.files["file"]

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise UploadError("Sorry, but that file isn't a supported video format.")
            
            os.makedirs("uploads", exist_ok=True)

            video_id = common.generate_key()

            file.save(pathlib.Path("uploads") / (video_id + ".upload"))

            return redirect("/", code=302)
        except UploadError as e:
            return render_template(
                "upload/upload.html",
                user=get_current_user(request),
                section="upload",
                allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
                error=str(e)
            )

    return render_template(
        "upload/upload.html",
        user=get_current_user(request),
        section="upload",
        allowed_mime_types=", ".join(ALLOWED_MIME_TYPES),
        error=""
    )