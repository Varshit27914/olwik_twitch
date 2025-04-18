from flask import Flask, jsonify, render_template_string
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string("""
        <!DOCTYPE html>
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
    try:
        subprocess.Popen(['python3', 'twitch_bot.py'])  # Make sure twitch_bot.py matches your filename
        return jsonify({'status': 'Olwik is now live on Twitch!'})
    except Exception as e:
        return jsonify({'status': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
