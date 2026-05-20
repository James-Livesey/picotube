from flask import Blueprint, render_template

auth = Blueprint("auth", __name__)

@auth.route("/signin")
def sign_in():
    return render_template(
        "auth/signin.html",
        section="signin"
    )

@auth.route("/signup")
def sign_up():
    return render_template(
        "auth/signup.html",
        section="signup"
    )