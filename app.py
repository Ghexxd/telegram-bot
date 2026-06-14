from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_data = {}

# -------------------------
# SEND MESSAGE
# -------------------------
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# -------------------------
# VALIDATION HELPERS
# -------------------------
def is_valid_age(text):
    return text.isdigit()

def is_valid_email(text):
    return "@" in text and "." in text

def normalize(text):
    return text.lower().strip()

# -------------------------
# WORKOUT GENERATOR
# -------------------------
def generate_workout(data):

    age = int(data["age"])
    level = data["level"]
    equipment = data["equipment"]
    goal = data["goal"]
    focus = data["focus"]
    days = data["days"]
    days_list = data["days_list"]

    # INTENSITY RULES
    if age < 18:
        intensity = "giovane"
    elif age <= 35:
        intensity = "alto"
    else:
        intensity = "protetto"

    text = f"🏋️ PROGRAMMA PERSONALIZZATO\n\n"
    text += f"🎯 Obiettivo: {goal}\n📊 Livello: {level}\n🏠 Attrezzatura: {equipment}\n🔥 Intensità: {intensity}\n\n"

    # FOR EACH DAY
    for d in days_list:

        text += f"\n📅 {d.upper()}\n"

        # SAFETY ADAPTATION
        if intensity == "protetto":
            safety = "⚠️ Esercizi controllati, niente impatti pesanti\n"
        elif intensity == "giovane":
            safety = "💪 Energia alta, focus tecnica\n"
        else:
            safety = "🔥 Intensità massima controllata\n"

        text += safety

        # FULL BODY
        if focus == "full body":

            if goal == "massa":
                text += """
- Squat 4x10
- Panca / Push-up 4x10
- Rematore 4x10
- Affondi 3x12
- Plank 3x40s
"""

            else:
                text += """
- Burpees 3x12
- Squat jump 3x12
- Push-up 3x10
- Mountain climber 30s
"""

        # UPPER BODY
        elif focus == "upper body":

            if goal == "massa":
                text += """
- Panca / Push-up 4x10
- Rematore 4x10
- Shoulder press 3x10
- Curl bicipiti 3x12
- Addome 3x15
"""
            else:
                text += """
- Push-up 4x max
- Dip 3x10
- Crunch 3x15
- Plank 40s
"""

        # LOWER BODY
        elif focus == "lower body":

            if goal == "massa":
                text += """
- Squat 4x10
- Affondi 4x10
- Leg press / bodyweight 4x12
- Glute bridge 3x15
- Calf raises 4x15
"""
            else:
                text += """
- Squat jump 3x12
- Affondi 3x12
- Step-up 3x12
- Wall sit 30s
"""

        text += "\n----------------------\n"

    text += "\n💡 Consiglio: aumenta gradualmente intensità ogni settimana."

    return text

# -------------------------
# WEBHOOK
# -------------------------
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = normalize(msg.get("text", ""))

    if chat_id not in user_data:
        user_data[chat_id] = {"step": 0, "data": {}}

    u = user_data[chat_id]

    # START
    if text == "/start":
        u["step"] = 1
        send(chat_id, "👤 Scrivi Nome e Cognome:")
        return "ok"

    # STEP 1 NAME
    if u["step"] == 1:
        u["data"]["name"] = text
        u["step"] = 2
        send(chat_id, "📧 Inserisci email:")
        return "ok"

    # STEP 2 EMAIL
    if u["step"] == 2:
        if not is_valid_email(text):
            send(chat_id, "❌ Email non valida, riprova:")
            return "ok"

        u["data"]["email"] = text
        u["step"] = 3
        send(chat_id, "🎂 Età?")
        return "ok"

    # STEP 3 AGE
    if u["step"] == 3:
        if not is_valid_age(text):
            send(chat_id, "❌ Inserisci un numero valido:")
            return "ok"

        u["data"]["age"] = text
        u["step"] = 4
        send(chat_id, "📊 Livello? (mai allenato / base / avanzato / esperto)")
        return "ok"

    # STEP 4 LEVEL
    if u["step"] == 4:
        u["data"]["level"] = text
        u["step"] = 5
        send(chat_id, "🏠 Attrezzatura? (corpo libero / casa / palestra)")
        return "ok"

    # STEP 5 EQUIPMENT
    if u["step"] == 5:
        if "casa" in text:
            send(chat_id, "🏠 Perfetto, userai manubri e barra trazioni se disponibili")
        u["data"]["equipment"] = text
        u["step"] = 6
        send(chat_id, "🎯 Obiettivo? (massa / dimagrimento)")
        return "ok"

    # STEP 6 GOAL
    if u["step"] == 6:
        u["data"]["goal"] = text
        u["step"] = 7
        send(chat_id, "🎯 Focus? (upper body / lower body / full body)")
        return "ok"

    # STEP 7 FOCUS
    if u["step"] == 7:
        u["data"]["focus"] = text
        u["step"] = 8
        send(chat_id, "📅 Quanti giorni a settimana vuoi allenarti?")
        return "ok"

    # STEP 8 DAYS NUMBER
    if u["step"] == 8:

        if not text.isdigit():
            send(chat_id, "❌ Scrivi un numero valido (es: 3, 4, 5)")
            return "ok"

        u["data"]["days"] = int(text)
        u["step"] = 9
        send(chat_id, "📅 Scrivi i giorni (es: lunedi, martedi, mercoledi):")
        return "ok"

    # STEP 9 DAYS LIST
    if u["step"] == 9:

        days_list = text.split(",")
        u["data"]["days_list"] = [d.strip() for d in days_list]

        workout = generate_workout(u["data"])

        send(chat_id, workout)

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"


# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return "Fitness Bot Attivo"