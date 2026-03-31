from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import os

from groq import Groq

# Safe import of olwik bot
try:
    import olwik
    OLWIK_AVAILABLE = True
except ImportError:
    OLWIK_AVAILABLE = False
    print("WARNING: olwik module not found. Twitch bot will be disabled.")

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Groq client — will raise clearly if key is missing
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY environment variable is not set!")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Bot state
bot_running = False


@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route('/')
def home():
    return render_template_string("""
        <html>
        <head><title>Olwik Bot</title></head>
        <body>
            <h2>Olwik Twitch Bot</h2>
            <button id="activateBtn">Activate Olwik</button>
            <p id="status"></p>
            <script>
            document.getElementById('activateBtn').addEventListener('click', async () => {
                const res = await fetch('/activate-olwik', { method: 'POST' });
                const data = await res.json();
                document.getElementById('status').innerText = data.status;
            });
            </script>
        </body>
        </html>
    """)


@app.route('/activate-olwik', methods=['POST'])
def activate_olwik():
    global bot_running
    if not OLWIK_AVAILABLE:
        return jsonify({'status': 'Olwik module not available on this server.'})
    if not bot_running:
        bot_running = True
        threading.Thread(target=olwik.run_bot, daemon=True).start()
        return jsonify({'status': 'Olwik is now live on Twitch!'})
    else:
        return jsonify({'status': 'Olwik is already running!'})


@app.route("/ask", methods=["POST", "OPTIONS"])
def ask():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    if not client:
        return jsonify({"error": "GROQ_API_KEY is not configured on the server."}), 500

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        user_msg = data.get("message", "").strip()
        if not user_msg:
            return jsonify({"error": "No message provided"}), 400

        # Build fresh per-request message list to avoid cross-user contamination
        messages = [
            {
                "role": "system",
                "content": (
                    "Your name is Olwik. You are a helpful, friendly AI assistant. "
                    "Your creator is Varshit. Your father's name is Sathwik. "
                    "There is a person called James who is the CEO of a group called Bomma. "
                    "Always reply as Olwik."
                )
            },
            {"role": "user", "content": user_msg}
        ]

        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=1024,
        )

        response_text = completion.choices[0].message.content
        return jsonify({"response": response_text})

    except Exception as e:
        print(f"ERROR in /ask route: {type(e).__name__}: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
