import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v23.0")


@app.route("/", methods=["GET"])
def home():
    return "Smart Reply AI server is running!", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json(silent=True) or {}

    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    sender = message.get("from")
                    if sender:
                        send_reply(
                            sender,
                            "سڵاو! پەیامەکەت گەیشت. تکایە کەمێک چاوەڕێ بکە."
                        )
    except Exception as error:
        app.logger.exception("Webhook error: %s", error)

    return "EVENT_RECEIVED", 200


def send_reply(recipient, message):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        app.logger.error("WhatsApp environment variables are missing")
        return

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message},
    }

    response = requests.post(
        url, headers=headers, json=payload, timeout=15
    )
    app.logger.info("WhatsApp API status: %s", response.status_code)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
