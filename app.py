from flask import Flask, request, jsonify, render_template_string
import threading
import olwik  # your Twitch bot module
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Initialize OpenAI
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

@app.route('/ask', methods=['POST'])
def ask():
    print("🔥 /ask endpoint hit!")  # For debugging in Render logs
    data = request.json
    user_input = data.get("message", "")
    
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    messages.append({"role": "user", "content": user_input})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        response = completion.choices[0].message.content
        messages.append({"role": "assistant", "content": response})
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
