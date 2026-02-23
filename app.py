from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "hello world", 200

@app.route("/health")
def health():
    return "ok", 200