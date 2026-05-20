import logging
import re
import bcrypt
import time
import hashlib
import jwt
from flask import Blueprint, request, render_template, make_response, redirect

import common
import db

auth = Blueprint("auth", __name__)
logger = logging.getLogger()
jwt_secret = common.generate_key(64)

class AuthError(Exception):
    pass

def authenticate_user(username, password):
    try:
        user = db.cursor.execute("SELECT uid, password FROM users WHERE username = ?", [username.lower()]).fetchone()
    except Exception as e:
        logger.error("Cannot authenticate user: %s", repr(e))

        raise AuthError("An unknown error occurred when trying to authenticate. Please try again later.")

    print(user)
    if user is None or not bcrypt.checkpw(password.encode(), user[1]):
        raise AuthError("Incorrect username or password. Try typing them in again, but be super careful this time.")

    return user[0]

def create_user(username, email, password, ip_address):
    uid = common.generate_key()

    if not email.find("@"):
        raise AuthError("The email address you entered doesn't look very email-address-like.")

    if not re.match(r"^[a-zA-Z0-9_-]{2,20}$", username):
        raise AuthError("Invalid username. Your username must be between 2 and 20 characters long, and can only contain lowercase and uppercase letters, digits, underscore (_) and hyphen (-).")

    if len(password) < 8:
        raise AuthError("Your password sucks. Please make it at least 8 characters long.")

    if db.cursor.execute("SELECT * FROM users WHERE username = ?", [username.lower()]).fetchone() is not None:
        raise AuthError("Someone else has that username already. Please try coming up with a different username instead.")

    try:
        db.cursor.execute(
            "INSERT INTO users (uid, username, display_username, email, password, created_time, network_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                uid,
                username.lower(),
                username,
                email,
                bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
                time.time(),
                hashlib.sha256(ip_address.encode()).hexdigest()
            ]
        )

        db.connection.commit()

        return uid
    except Exception as e:
        logger.error("Cannot create user: %s", repr(e))

        raise AuthError("An unknown error occurred when trying to create this user. Please try again later.")

def get_current_user(request):
    token = request.cookies.get("picotube_token")

    if token is None:
        return None

    try:
        return jwt.decode(token, jwt_secret, algorithms=["HS256"])
    except Exception as e:
        logger.warning("Unable to decode JWT for current user: %s", repr(e))

        return None

def generate_user_token(uid):
    user = db.cursor.execute("SELECT username FROM users WHERE uid = ?", [uid]).fetchone()

    if user is None:
        logging.error("Unknown user ID when generating user token: %s", uid)

        return None

    return jwt.encode({
        "uid": uid,
        "username": user[0]
    }, jwt_secret, algorithm="HS256")

@auth.route("/signin", methods=["GET", "POST"])
def sign_in():
    if get_current_user(request):
        return redirect("/", code=302)

    if request.method == "POST":
        try:
            uid = authenticate_user(request.form["username"], request.form["password"])
            token = generate_user_token(uid)
            response = make_response(redirect("/", code=302))

            response.set_cookie("picotube_token", token)

            return response
        except AuthError as e:
            return render_template(
                "auth/signin.html",
                section="signin",
                username=request.form["username"],
                error=str(e)
            )

    return render_template(
        "auth/signin.html",
        section="signin",
        username="",
        error=""
    )

@auth.route("/signup", methods=["GET", "POST"])
def sign_up():
    if get_current_user(request):
        return redirect("/", code=302)

    if request.method == "POST":
        try:
            if request.form["passwordAgain"] != request.form["password"]:
                raise AuthError("The passwords you entered don't match. Make sure you type it in super slowly and carefully this time. It's important, because otherwise you're going to mess it up and you'll never be able to get into your account again.")

            if request.form["tosAgreed"] != "on":
                raise AuthError("You actually have to tick the box to promise that you won't do anything bad. You can't just get out of it...")

            uid = create_user(request.form["username"], request.form["email"], request.form["password"], request.remote_addr)
            token = generate_user_token(uid)
            response = make_response(redirect("/", code=302))

            response.set_cookie("picotube_token", token)

            return response
        except AuthError as e:
            return render_template(
                "auth/signup.html",
                user=None,
                section="signup",
                email=request.form["email"],
                username=request.form["username"],
                tosAgreed=request.form["tosAgreed"],
                error=str(e)
            )

    return render_template(
        "auth/signup.html",
        user=None,
        section="signup",
        email="",
        username="",
        tosAgreed="off",
        error=""
    )

@auth.route("/signout")
def sign_out():
    response = make_response(redirect("/", code=302))

    response.set_cookie("picotube_token", "", expires=0)

    return response