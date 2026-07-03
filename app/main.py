import logging
from flask import Flask, request, render_template

import db
from privateapi import privateapi
from auth import auth, get_current_user
from upload import upload
from watch import watch
from recommendations import get_recommendations
from channel import channel

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
logger = logging.getLogger()

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.register_blueprint(privateapi)
app.register_blueprint(auth)
app.register_blueprint(upload)
app.register_blueprint(watch)
app.register_blueprint(channel)

@app.after_request
def after_request(response):
    response.headers.add("Cross-Origin-Embedder-Policy", "require-corp")
    response.headers.add("Cross-Origin-Opener-Policy", "same-origin")

    return response

@app.route("/")
def index():
    return render_template(
        "index.html",
        user=get_current_user(request),
        section="home",
        recommendations=get_recommendations(limit=8)
    )

if __name__ == "__main__":
    db.init()

    app.run(debug=True, host="0.0.0.0", port=8000)