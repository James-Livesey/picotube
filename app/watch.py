import logging
import pathlib
from flask import Blueprint, request, render_template, abort, send_from_directory

import db
from auth import get_current_user
from recommendations import get_recommendations

watch = Blueprint("watch", __name__)
logger = logging.getLogger()

def get_video_details(video):
    try:
        db.lock.acquire(True)

        fields = [
            "author",
            "title",
            "description",
            "created_time",
            "has_burnt_in_subtitles",
            "has_flashing_images",
            "allows_comments",
            "published",
            "removed",
            "processing_done"
        ]

        row = db.cursor.execute(f"SELECT {', '.join(fields)} FROM videos WHERE video_id = ?", [video]).fetchone()
        video = {}

        if row is None:
            return None

        for i in range(0, len(fields)):
            video[fields[i]] = row[i]

        return video
    finally:
        db.lock.release()

def get_video_variants(video):
    try:
        db.lock.acquire(True)

        fields = [
            "variant_id",
            "type",
            "display_name",
            "transcoder_status"
        ]

        rows = db.cursor.execute(f"SELECT {', '.join(fields)} FROM video_variants WHERE video = ?", [video]).fetchall()
        variants = []

        for row in rows:
            variant = {}

            for i in range(0, len(fields)):
                variant[fields[i]] = row[i]

            variants.append(variant)

        return variants
    finally:
        db.lock.release()

def get_video_subtitles(video):
    try:
        db.lock.acquire(True)

        fields = [
            "subtitles_id",
            "type",
            "display_name"
        ]

        rows = db.cursor.execute(f"SELECT {', '.join(fields)} FROM video_subtitles WHERE video = ?", [video]).fetchall()
        variants = []

        for row in rows:
            variant = {}

            for i in range(0, len(fields)):
                variant[fields[i]] = row[i]

            variants.append(variant)

        return variants
    finally:
        db.lock.release()

@watch.route("/watch/<video_id>")
def watch_video(video_id):
    user = get_current_user(request)
    video = get_video_details(video_id)

    if video is None:
        return abort(404)

    if not video["published"] and (user is None or user["uid"] != video["author"]):
        return abort(404)

    variants = get_video_variants(video_id)
    original_variant = None

    for variant in variants:
        if variant["type"] == "original":
            original_variant = variant

            break

    subtitles_list = get_video_subtitles(video_id)
    generated_subtitles = None

    for subtitles in subtitles_list:
        if subtitles["type"] == "generated":
            generated_subtitles = subtitles

            break

    return render_template(
        "watch/watch.html",
        user=get_current_user(request),
        section="watch",
        video_id=video_id,
        video=video,
        variants=variants,
        original_variant=original_variant,
        subtitles=subtitles_list,
        generated_subtitles=generated_subtitles,
        recommendations=get_recommendations(["videos.video_id != ?"], [video_id], limit=4)
    )

@watch.route("/watch/<video_id>/<path:path>")
def watch_file(video_id, path):
    return send_from_directory(pathlib.Path("..") / "videos", pathlib.Path(video_id) / path)