import logging
import os
import pathlib
import time
import re
import ffmpeg
import cv2
from flask import Blueprint, request, render_template, redirect, abort

import common
import db
from auth import get_current_user

upload = Blueprint("upload", __name__)
logger = logging.getLogger()

ALLOWED_MIME_TYPES = ["video/mp4", "video/x-matroska", "video/webm", "video/x-msvideo", "video/quicktime"]

class UploadError(Exception):
    pass

def create_variant(video, duration):
    variant_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO video_variants (variant_id, video, duration) VALUES (?, ?, ?)", [variant_id, video, int(duration * 1000)])

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

        raise UploadError("An unknown error occurred when trying to create subtitles for your video. Please try again later.")
    finally:
        db.lock.release()

def create_video(author, title, duration):
    video_id = common.generate_key()

    try:
        db.lock.acquire(True)

        db.cursor.execute("INSERT INTO videos (video_id, author, title, created_time, duration) VALUES (?, ?, ?, ?, ?)", [
            video_id,
            author,
            title,
            time.time(),
            int(duration * 1000)
        ])

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot create video: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to create your video. Please try again later.")
    finally:
        db.lock.release()

    return video_id

def update_video_details(video, title, description, has_burnt_in_subtitles, has_flashing_images, allows_comments, published):
    try:
        db.lock.acquire(True)

        db.cursor.execute(
            "UPDATE videos SET title = ?, description = ?, has_burnt_in_subtitles = ?, has_flashing_images = ?, allows_comments = ?, published = ? WHERE video_id = ?",
            [
                title,
                description,
                has_burnt_in_subtitles,
                has_flashing_images,
                allows_comments,
                published,
                video
            ]
        )

        db.connection.commit()
    except Exception as e:
        logger.error("Cannot update video details: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to update your video's details. Please try again later.")
    finally:
        db.lock.release()

def add_video_tags(video, tags):
    try:
        db.lock.acquire(True)

        for display_name in tags:
            tag = re.sub(r"[^a-z0-9]", "", display_name.lower())

            if len(tag) == 0:
                continue

            db.cursor.execute("INSERT OR IGNORE INTO tags (tag, display_name) VALUES (?, ?)", [tag, display_name])
            db.cursor.execute("INSERT OR IGNORE INTO video_tags (video, tag) VALUES (?, ?)", [video, tag])

            db.connection.commit()
    except Exception as e:
        logger.error("Cannot add tag: %s", repr(e))

        raise UploadError("An unknown error occurred when trying to add tags to your video. Please try again later.")
    finally:
        db.lock.release()

@upload.route("/upload", methods=["GET", "POST"])
def upload_area():
    user = get_current_user(request)

    if user is None:
        return redirect("/signin?go=/upload", code=302)

    if request.method == "POST":
        os.makedirs("uploads", exist_ok=True)

        provisional_variant_id = common.generate_key()
        provisional_path = pathlib.Path("uploads") / (provisional_variant_id + ".upload.temp")

        try:
            if "file" not in request.files or request.files["file"].filename == "":
                raise UploadError("Please actually upload something.")

            file = request.files["file"]
            subtitles = request.form.get("subtitles") or ""

            if file.content_type not in ALLOWED_MIME_TYPES:
                raise UploadError("Sorry, but that file isn't a supported video format.")

            file.save(provisional_path)

            probe = ffmpeg.probe(provisional_path)

            width = None
            height = None
            duration = None

            for stream in probe["streams"]:
                if stream["codec_type"] == "video":
                    width = stream["width"]
                    height = stream["height"]
                    duration = float(stream["duration"])

                    break

            if width is None or height is None or duration is None:
                raise UploadError("Sorry, but this video file doens't actually seem to contain any video data. Please try a different file.")

            if duration > 5 * 60:
                raise UploadError("Sorry, but this video is too long. Please try uploading a shorter video.")

            if width < 256 or height < 144:
                raise UploadError("Sorry, but video files must have a minimum resolution of 256×144. Please increase the video file's resolution and try again.")

            if width > 854 or height > 480:
                raise UploadError("Sorry, but video files must have a maximum resolution of 854×480. Please reduce the video file's resolution and try again.")

            video_id = create_video(user["uid"], os.path.splitext(file.filename)[0], duration)
            variant_id = create_variant(video_id, duration)

            if subtitles != "":
                create_subtitles(video_id, "generated", subtitles)

            try:
                capture = cv2.VideoCapture(provisional_path)

                capture.set(cv2.CAP_PROP_POS_MSEC, (duration / 5) * 1000)

                success, image = capture.read()

                os.makedirs(pathlib.Path("videos") / video_id, exist_ok=True)

                if success:
                    cv2.imwrite(pathlib.Path("videos") / video_id / "thumbnail.jpg", image)
                else:
                    raise Exception("Read unsuccessful")
            except Exception as e:
                logger.warning("Failed to generate thumbnail: %s", e)

            os.rename(provisional_path, pathlib.Path("uploads") / (variant_id + ".upload"))

            return redirect("/upload/" + video_id, code=302)
        except UploadError as e:
            try:
                os.remove(provisional_path)
            except Exception as e:
                logger.warning("Failed to remove provisional video file: %s", e)

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

@upload.route("/upload/<video_id>", methods=["GET", "POST"])
def upload_details(video_id):
    user = get_current_user(request)

    if user is None:
        return redirect("/signin?go=/upload/" + video_id, code=302)

    try:
        db.lock.acquire(True)

        video = db.cursor.execute("SELECT author, title, description FROM videos WHERE video_id = ?", [video_id]).fetchone()
    finally:
        db.lock.release()

    if video is None:
        return abort(404)

    if user["uid"] != video[0]:
        return abort(404)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = request.form.get("description") or ""
        tags = request.form.get("tags") or ""
        subtitles = request.form.get("subtitles") or "useGenerated"
        flashing_images = request.form.get("flashingImages") or ""
        comments = request.form.get("comments") or "yes"
        publish = request.form.get("publish") or "now"

        try:
            if len(title) == 0:
                raise UploadError("You haven't provided a video title. Please add one.")

            if len(title) > 100:
                raise UploadError("The video title is too long. Please cut it down so that it fits within 100 characters.")

            if len(description) > 2000:
                raise UploadError("The video description is too long. Please cut it down so that it fits within 2,000 characters.")

            tag_list = []

            for tag in tags.split(","):
                tag = tag.strip()

                if tag == "":
                    continue

                if len(tag) > 20:
                    raise UploadError(f"The tag '{tag}' is too long. Please make this tag at most 20 characters long.")

                tag_list.append(tag)

            if len(tag_list) > 10:
                raise UploadError("You've got too many tags. You can only have up to 10 tags per video.")

            if flashing_images not in ["yes", "no"]:
                raise UploadError("Please indicate whether this video contains flashing images or not.")

            update_video_details(
                video_id,
                title,
                description,
                subtitles == "burntIn",
                flashing_images == "yes",
                comments == "yes",
                publish == "now"
            )

            add_video_tags(video_id, tag_list)

            if subtitles == "upload":
                if "subtitlesFile" not in request.files or request.files["subtitlesFile"].filename == "":
                    raise UploadError("You forgot to upload the subtitles file. Please add it or instead select another subtitles option.")

                create_subtitles(video_id, "original", request.files["subtitlesFile"].read().decode())

            return redirect("/watch/" + video_id, code=302)
        except UploadError as e:
            return render_template(
                "upload/uploaddetails.html",
                user=user,
                section="upload",
                title=title,
                description=description,
                tags=tags,
                subtitles=subtitles,
                flashing_images=flashing_images,
                comments=comments,
                publish=publish,
                error=str(e)
            ), 400

    return render_template(
        "upload/uploaddetails.html",
        user=user,
        section="upload",
        title=video[1] or "",
        description=video[2] or "",
        tags="",
        subtitles="useGenerated",
        flashing_images="",
        comments="yes",
        publish="now",
        error=""
    )