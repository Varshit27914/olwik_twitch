from flask import Flask
import threading

app = Flask(__name__)

@app.route("/start-bot", methods=["POST"])
def start_bot_endpoint():
    threading.Thread(target=run_bot).start()
    return {"status": "Bot started"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
