from flask import Flask

app = Flask(__name__)


@app.route("/")
def root_route():
    return "Root Route"


app.run(host="0.0.0.0", port=5000, debug=True)
