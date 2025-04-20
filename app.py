from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import os
from openai import OpenAI
import olwik  # Your Twitch bot module

app = Flask(__name__)

# CORS: Allow all origins (or specify your frontend)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# OpenAI init
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
messages = [{"role": "system", "content": "You're a helpful assistant."}]
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

@app.route('/activate-olwik', methods=['POST'])
def activate_olwik():
    global bot_running
    if not bot_running:
        bot_running = True
        threading.Thread(target=olwik.run_bot, daemon=True).start()
        return jsonify({'status': 'Olwik is now live on Twitch!'})
    else:
        return jsonify({'status': 'Olwik is already running!'})

messages = [{"role": "system", "content": "You're a helpful assistant."}]

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_msg = data.get("message")

        if not user_msg:
            return jsonify({"error": "No message provided"}), 400

        messages.append({"role": "user", "content": user_msg})

        # Call OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-3.5-turbo"
            messages=messages
        )

        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})

        return jsonify({"response": response})

    except Exception as e:
        print("🔥 ERROR in /ask route:", str(e))  # Print error to console
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

