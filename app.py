from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import threading
import olwik
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins=["http://localhost:5500", "https://voice-assistant-api-exhp.onrender.com"])

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

messages = [{"role": "system", "content": "You're a helpful assistant."}]
bot_running = False

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
    if not bot_running:
        bot_running = True
        threading.Thread(target=olwik.run_bot, daemon=True).start()
        return jsonify({'status': 'Olwik is now live on Twitch!'})
    else:
        return jsonify({'status': 'Olwik is already running!'})

@app.route("/ask", methods=["POST", "OPTIONS"])
def ask():
    if request.method == "OPTIONS":
        # Handle CORS preflight
        response = jsonify({'status': 'CORS preflight successful'})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5500")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    data = request.get_json()
    user_msg = data.get("message")

    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    messages.append({"role": "user", "content": user_msg})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})

        result = jsonify({"response": response})
        result.headers.add("Access-Control-Allow-Origin", "http://localhost:5500")
        result.headers.add("Access-Control-Allow-Headers", "Content-Type")
        result.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return result
    except Exception as e:
        error_response = jsonify({"error": str(e)})
        error_response.headers.add("Access-Control-Allow-Origin", "http://localhost:5500")
        return error_response, 500

if __name__ == '__main__':
    app.run(debug=True)
