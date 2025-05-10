from flask import Flask, render_template_string, request, jsonify
import requests
import time

app = Flask(__name__)
cancel_requested = False

# HTML template as a string with improved styling, organization, and error messages
html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eliminador de Mensajes de Discord</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            transition: background-color 0.3s, color 0.3s;
        }
        .light {
            background-color: #f4f4f4;
            color: #333;
        }
        .dark {
            background-color: #121212;
            color: #e0e0e0;
        }
        .container {
            max-width: 500px;
            margin: 40px auto;
            padding: 30px;
            border-radius: 12px;
            background-color: inherit;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
        }
        h1 {
            color: #007bff;
            text-align: center;
        }
        label {
            margin-top: 15px;
            display: block;
        }
        input {
            width: 100%;
            padding: 12px;
            margin-top: 5px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 16px;
        }
        button {
            margin-top: 20px;
            padding: 12px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #0056b3;
        }
        #result, .error, .success {
            margin-top: 20px;
            font-weight: bold;
            text-align: center;
        }
        .error {
            color: #ff4d4d;
        }
        .success {
            color: #00cc66;
        }
        #progress-container {
            margin-top: 20px;
            height: 25px;
            width: 100%;
            background: #ccc;
            border-radius: 12px;
            overflow: hidden;
        }
        #progress-bar {
            height: 100%;
            width: 0%;
            background-color: #007bff;
            color: white;
            text-align: center;
            line-height: 25px;
            transition: width 0.4s ease;
        }
        .theme-toggle {
            float: right;
            margin-top: -50px;
        }
        .counts {
            margin-top: 10px;
            text-align: center;
        }
        ul {
            margin-top: 15px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 14px;
        }
    </style>
</head>
<body class="dark">
    <div class="container">
        <h1>Eliminador de Mensajes de Discord</h1>
        <button class="theme-toggle" onclick="toggleTheme()">🌓 Cambiar Tema</button>
        <form id="delete-form">
            <label for="user_id">ID de Usuario:</label>
            <input type="text" id="user_id" name="user_id" required>

            <label for="channel_id">ID del Canal:</label>
            <input type="text" id="channel_id" name="channel_id" required>

            <label for="session_token">Token de Sesión:</label>
            <input type="text" id="session_token" name="session_token" required>

            <button type="submit">Eliminar Mensajes</button>
            <button type="button" onclick="cancelProcess()">❌ Cancelar</button>
        </form>

        <div id="result">Esperando acción...</div>
        <div id="progress-container">
            <div id="progress-bar">0%</div>
        </div>

        <div class="counts">
            Eliminados: <span id="deleted">0</span> /
            Total: <span id="total">0</span> |
            Pendientes: <span id="pending">0</span>
        </div>

        <ul id="deleted-list"></ul>
        <div id="error-message" class="error"></div>
        <div id="success-message" class="success"></div>
    </div>

    <script>
        let totalCount = 0, deletedCount = 0;
        let cancelRequested = false;

        function toggleTheme() {
            document.body.classList.toggle("light");
            document.body.classList.toggle("dark");
        }

        function cancelProcess() {
            cancelRequested = true;
            document.getElementById("result").innerText = "⏹️ Proceso cancelado por el usuario.";
        }

        document.getElementById('delete-form').addEventListener('submit', async function(event) {
            event.preventDefault();
            cancelRequested = false;

            deletedCount = 0;
            totalCount = 0;
            document.getElementById("deleted").innerText = "0";
            document.getElementById("total").innerText = "0";
            document.getElementById("pending").innerText = "0";
            document.getElementById("progress-bar").style.width = "0%";
            document.getElementById("progress-bar").innerText = "0%";
            document.getElementById("deleted-list").innerHTML = "";
            document.getElementById("error-message").innerText = "";
            document.getElementById("success-message").innerText = "";
            document.getElementById("result").innerText = "🔄 Eliminando mensajes...";

            const userId = document.getElementById('user_id').value;
            const channelId = document.getElementById('channel_id').value;
            const token = document.getElementById('session_token').value;

            const response = await fetch('/delete_messages', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, channel_id: channelId, session_token: token })
            });

            const data = await response.json();

            if (data.error) {
                document.getElementById("error-message").innerText = data.error;
                document.getElementById("result").innerText = "";
                return;
            }

            totalCount = data.total;
            document.getElementById("total").innerText = totalCount;

            for (let i = 0; i < data.deleted_messages.length; i++) {
                if (cancelRequested) break;
                const li = document.createElement("li");
                li.textContent = data.deleted_messages[i];
                document.getElementById("deleted-list").appendChild(li);
                deletedCount++;
                const percent = Math.floor((deletedCount / totalCount) * 100);
                document.getElementById("deleted").innerText = deletedCount;
                document.getElementById("pending").innerText = totalCount - deletedCount;
                document.getElementById("progress-bar").style.width = percent + "%";
                document.getElementById("progress-bar").innerText = percent + "%";
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            if (!cancelRequested) {
                document.getElementById("result").innerText = "";
                document.getElementById("success-message").innerText = "✅ Eliminación completada.";
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Renderiza la página principal con el formulario para eliminar mensajes."""
    return render_template_string(html_template)


@app.route('/cancel', methods=['POST'])
def cancel():
    global cancel_requested
    cancel_requested = True
    return '', 204


@app.route('/delete_messages', methods=['POST'])
def delete_messages():
    global cancel_requested
    cancel_requested = False

    data = request.json
    user_id = data['user_id']
    channel_id = data['channel_id']
    session_token = data['session_token']

    deleted_messages = []
    last_message_id = None
    total_found = 0

    try:
        while True:
            if cancel_requested:
                break

            url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=50"
            if last_message_id:
                url += f"&before={last_message_id}"

            headers = {"Authorization": session_token}
            res = requests.get(url, headers=headers)
            messages = res.json()

            if not messages or 'message' in messages:
                break

            for message in messages:
                if cancel_requested:
                    break

                if message['author']['id'] == user_id:
                    try:
                        delete_url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message['id']}"
                        requests.delete(delete_url, headers=headers)
                        deleted_messages.append(message.get('content', '[Mensaje eliminado]'))
                        total_found += 1
                        time.sleep(1.5)
                    except:
                        continue

            last_message_id = messages[-1]['id']
            if len(messages) < 50:
                break

        return jsonify({'deleted_messages': deleted_messages, 'total': total_found})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)