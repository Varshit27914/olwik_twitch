from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import os
from groq import Groq
import olwik  # Your Twitch bot module

app = Flask(__name__)

# Enable CORS
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Chat memory
messages = [{"role": "system", "content": "You're a helpful assistant."}]

# Bot state
bot_running = False


# Apply CORS headers manually (extra safety)
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# Home page
@app.route('/')
def home():
    return render_template_string("""
        <html>
        <head><title>Olwik Bot</title></head>
        <body>
            <h2>Olwik Twitch Bot:</h2>
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


# Activate Twitch bot
@app.route('/activate-olwik', methods=['POST'])
def activate_olwik():
    global bot_running
    if not bot_running:
        bot_running = True
        threading.Thread(target=olwik.run_bot, daemon=True).start()
        return jsonify({'status': 'Olwik is now live on Twitch!'})
    else:
        return jsonify({'status': 'Olwik is already running!'})


# AI Chat endpoint (Groq)
@app.route("/ask", methods=["POST"])
def ask():
    global messages

    try:
        data = request.get_json()
        user_msg = data.get("message")

        if not user_msg:
            return jsonify({"error": "No message provided"}), 400

        # Add user message
        messages.append({"role": "user", "content": user_msg})

        # Call Groq API
        completion = client.chat.completions.create(
            model="llama3-70b-8192",  # or "llama3-8b-8192"
            messages=messages
        )

        response = completion.choices[0].message.content

        # Store response
        messages.append({"role": "assistant", "content": response})

        return jsonify({"response": response})

    except Exception as e:
        print("🔥 ERROR in /ask route:", str(e))
        return jsonify({"error": str(e)}), 500


# Run server
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
