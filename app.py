from flask import Flask, request, jsonify
import requests
import os
# from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurar credenciales
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# verify webhook endpoint
@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook Verified")
        return challenge, 200
    return 'Forbidden', 403

# Process incoming messages endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data['entry'][0]['changes'][0]['value']['messages'][0]
    phone_number_id = data['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']
    from_number = message['from']  # destinatary number
    msg_body = message['text']['body']  # message

    print("Mensaje recibido:", msg_body)

    # request to Ollama apu to analyze the promt
    ollama_response = analyze_with_ollama(msg_body)

    # send mesage to wpp
    send_message(from_number, phone_number_id, ollama_response)

    return 'EVENT_RECEIVED', 200

def analyze_with_ollama(text):
    data = {
        "content": "Eres un experto en ataques de phising y debes ser capaz de determinar cuando alguien está siendo víctima de algún ataque de este estilo. Tienes la capacidad de indagar más a fondo para lograr dar un veredicto. Debes ser puntual y conciso",
        "prompt": text
    }

    response = requests.post("https://api.ollama.com/analyze", json=data)
    
    if response.status_code == 200:
        analysis = response.json().get("analysis", "No se pudo analizar el mensaje.")
        return analysis
    else:
        print("Error en Ollama API:", response.status_code, response.text)
        return "Hubo un error al analizar el mensaje."

def send_message(to, phone_number_id, message):
    url = f"https://graph.facebook.com/v15.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Mensaje enviado:", message)
    else:
        print("Error al enviar mensaje:", response.status_code, response.text)
