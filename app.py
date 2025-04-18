from flask import Flask, render_template, request
import threading
from olwik import run_bot  # Import the bot function
import os


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    threading.Thread(target=run_bot).start()
    return "Olwik started!"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
