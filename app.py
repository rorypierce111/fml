from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "home", 200

@app.route("/health")
def health():
    return "ok", 200