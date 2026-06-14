from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_data = {}

def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


def build_workout(a):

    obiettivo = a["obiettivo"]
    livello = a["livello"]
    split = a["split"]
    eta = a["eta"]
    att = a["attrezzatura"]

    base = ""

    # ---------------- MASSA ----------------
    if "massa" in obiettivo:

        if livello == "mai allenato":
            if split == "full body":
                base = """
FULL BODY A
- Squat 3x10
- Push-up 3x8
- Rematore 3x10
- Plank 3x20s

FULL BODY B
- Affondi 3x10
- Push-up inclinati 3x8
- Crunch 3x12
- Superman 3x12
"""

        elif livello == "base":
            if split == "upper body":
                base = """
UPPER A
- Panca / push-up 4x10
- Rematore 4x10
- Shoulder press 3x10
- Curl 3x12

UPPER B
- Dip 3x max
- Lat machine 4x10
- Addome 3x15
"""

            elif split == "lower body":
                base = """
LOWER A
- Squat 4x10
- Affondi 3x12
- Leg press 4x10
- Calf raises 4x15

LOWER B
- Stacco rumeno 3x10
- Glute bridge 3x12
- Leg curl 3x12
"""

            else:
                base = """
FULL BODY A
- Squat 4x10
- Panca 4x10
- Lat machine 4x10
- Plank 40s

FULL BODY B
- Squat jump
- Rematore
- Affondi
- Addome
"""

    # ---------------- DIMAGRIMENTO ----------------
    elif "dimagr" in obiettivo:

        if livello == "mai allenato":
            base = """
FULL BODY A
- Camminata 10 min
- Squat 3x12
- Push-up 3x8
- Plank 20s

FULL BODY B
- Jumping jack
- Crunch
- Mountain climber lento
- Step sul posto
"""

        elif livello == "base":
            base = """
HIIT A
- Burpees 3x10
- Squat 3x12
- Push-up 3x10
- Plank 40s

HIIT B
- Circuito 5 giri
- Jump squat
- Mountain climber
- Crunch
"""

        else:
            base = """
HIIT AVANZATO A
- Burpees 4x12
- Squat jump
- Push-up max
- Plank 1 min

HIIT B
- Tabata training
- Sprint
- Circuito full body
"""

    # ETA MODIFIER
    if "35" in eta:
        base += "\n⚠️ Consiglio: riduci impatto e aumenta recuperi"
    if "18" in eta and "sotto" in eta:
        base += "\n⚠️ Focus tecnica, niente carichi pesanti"

    return base


@app.route("/")
def home():
    return "Bot attivo"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").lower()

    if chat_id not in user_data:
        user_data[chat_id] = {"step": 0, "data": {}}

    u = user_data[chat_id]

    # START
    if text == "/start":
        u["step"] = 1
        send(chat_id, "💪 Obiettivo? (massa / dimagrimento)")
        return "ok"

    # STEP 1
    if u["step"] == 1:
        u["data"]["obiettivo"] = text
        u["step"] = 2
        send(chat_id, "📊 Livello? (mai allenato / base / avanzato / esperto)")
        return "ok"

    # STEP 2
    if u["step"] == 2:
        u["data"]["livello"] = text
        u["step"] = 3
        send(chat_id, "🏋️ Split? (full body / upper body / lower body)")
        return "ok"

    # STEP 3
    if u["step"] == 3:
        u["data"]["split"] = text
        u["step"] = 4
        send(chat_id, "🎂 Età? (sotto 18 / sopra 18 / sopra 35)")
        return "ok"

    # STEP 4
    if u["step"] == 4:
        u["data"]["eta"] = text
        u["step"] = 5
        send(chat_id, "🏠 Attrezzatura? (corpo libero / casa / palestra)")
        return "ok"

    # STEP 5 → GENERA
    if u["step"] == 5:
        u["data"]["attrezzatura"] = text

        workout = build_workout(u["data"])

        send(chat_id, f"🏋️ Ecco la tua scheda:\n\n{workout}")

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"