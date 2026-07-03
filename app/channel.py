import logging
import pathlib
from flask import Blueprint, request, render_template, abort, redirect

import db
from auth import get_current_user
from recommendations import get_recommendations

channel = Blueprint("channel", __name__)
logger = logging.getLogger()

def get_channel_user(username):
    try:
        db.lock.acquire(True)

        fields = [
            "uid",
            "display_username",
            "created_time",
            "admin",
            "favourite_colour"
        ]

        row = db.cursor.execute(f"SELECT {', '.join(fields)} FROM users WHERE username = ?", [username.lower()]).fetchone()
        user = {}

        if row is None:
            return None

        for i in range(0, len(fields)):
            user[fields[i]] = row[i]

        return user
    finally:
        db.lock.release()

@channel.route("/channel/<username>")
def view_channel(username):
    user = get_current_user(request)
    channel_user = get_channel_user(username)

    if channel_user is None:
        return abort(404)

    return render_template(
        "profile/channel.html",
        user=get_current_user(request),
        section="profile" if channel_user["uid"] == user["uid"] else "channel",
        channel_user=channel_user,
        videos=get_recommendations(["videos.author = ?"], [channel_user["uid"]], limit=1000)
    )

@channel.route("/profile")
def profile():
    user = get_current_user(request)

    if user is None:
        return redirect("/signin?go=/profile", code=302)

    return redirect(f"/channel/{user["username"]}", code=302)