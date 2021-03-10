from flask import Flask


app = Flask(__name__)


@app.route("/")
def root_route():
    return "Root Route"
