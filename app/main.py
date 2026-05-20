import logging
from flask import Flask, render_template

from auth import auth

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
logger = logging.getLogger()

app.register_blueprint(auth)

@app.route("/")
def index():
    return render_template(
        "index.html",
        section="home"
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)