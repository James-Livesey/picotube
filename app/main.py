import logging
from flask import Flask, request, render_template

import db
from privateapi import privateapi
from auth import auth, get_current_user
from upload import upload

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
logger = logging.getLogger()

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

app.register_blueprint(privateapi)
app.register_blueprint(auth)
app.register_blueprint(upload)

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
        section="home"
    )

if __name__ == "__main__":
    db.init()

    app.run(debug=True, host="0.0.0.0", port=8000)