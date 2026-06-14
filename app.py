from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_data = {}

# =========================
# SEND MESSAGE
# =========================
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def norm(t):
    return t.lower().strip()

def is_num(x):
    return x.isdigit()

# =========================
# VALIDATION
# =========================
def valid_age(a): return 10 <= a <= 99
def valid_weight(w): return 40 <= w <= 300

def valid_goal(x):
    return x in ["massa", "dimagrimento"]

# =========================
# WORKOUT LOGIC (SENZA RANDOM)
# =========================
def get_plan(goal, days):

    if goal == "massa":

        if days == 1:
            return ["FULL BODY"]

        if days == 2:
            return ["UPPER BODY", "LOWER BODY"]

        if days == 3:
            return ["PUSH", "PULL", "LEGS"]

        if days == 4:
            return ["PUSH", "PULL", "LEGS", "FULL BODY"]

        if days == 5:
            return ["PUSH", "PULL", "LEGS", "UPPER BODY", "LOWER BODY"]

        return ["PUSH", "PULL", "LEGS", "UPPER BODY", "LOWER BODY", "FULL BODY"]

    else:

        if days == 1:
            return ["HIIT FULL BODY"]

        if days == 2:
            return ["HIIT", "CARDIO"]

        if days == 3:
            return ["HIIT", "CIRCUIT", "CARDIO"]

        if days == 4:
            return ["HIIT", "UPPER TONING", "LOWER TONING", "CARDIO"]

        return ["HIIT", "CARDIO", "CIRCUIT", "CORE", "ACTIVE RECOVERY"]


# =========================
# EXERCISES (LOGICI)
# =========================
def build_workout(day_type):

    if day_type == "PUSH":
        return [
            "panca piana 4x8-10",
            "shoulder press 3x10",
            "dip 3x max",
            "alzate laterali 3x12"
        ]

    if day_type == "PULL":
        return [
            "lat machine 4x10",
            "rematore 4x10",
            "curl bicipiti 3x12",
            "face pull 3x15"
        ]

    if day_type == "LEGS":
        return [
            "squat 4x10",
            "affondi 3x12",
            "leg press 4x10",
            "calf raises 4x15"
        ]

    if day_type == "FULL BODY":
        return [
            "squat 4x10",
            "panca 4x10",
            "rematore 4x10",
            "plank 3x45s"
        ]

    if "UPPER" in day_type:
        return [
            "panca 4x10",
            "lat machine 4x10",
            "shoulder press 3x10",
            "curl + tricipiti 3x12"
        ]

    if "LOWER" in day_type:
        return [
            "squat 4x10",
            "leg press 4x10",
            "stacco rumeno 3x10",
            "calf raises 4x15"
        ]

    if "HIIT" in day_type:
        return [
            "burpees 12x",
            "squat jump 15x",
            "mountain climber 30s",
            "plank 45s"
        ]

    if "CARDIO" in day_type:
        return [
            "corsa 10-20 min",
            "corda 5 min",
            "jumping jack 1 min",
            "core leggero"
        ]

    if "CORE" in day_type:
        return [
            "plank",
            "crunch",
            "leg raise",
            "ab twist"
        ]

    return ["riposo attivo"]

# =========================
# GENERATOR
# =========================
def generate(data):

    name = data["name"]
    age = int(data["age"])
    weight = int(data["weight"])
    goal = data["goal"]
    days = data["days"]
    days_list = data["days_list"]

    plan = get_plan(goal, days)

    text = f"""
🏋️ PIANO PERSONALIZZATO

👤 {name}
🎯 {goal}
⚖️ {weight} kg
📅 giorni: {days}

"""

    for i in range(days):

        day_name = days_list[i]
        day_type = plan[i]

        text += f"\n📅 {day_name.upper()} — {day_type}\n"

        exercises = build_workout(day_type)

        for ex in exercises:
            text += f"- {ex}\n"

        text += "\n-------------------\n"

    return text


# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json
    if "message" not in data:
        return "ok"

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = norm(msg.get("text", ""))

    if chat_id not in user_data:
        user_data[chat_id] = {"step": 0, "data": {}}

    u = user_data[chat_id]

    # START
    if text == "/start":
        u["step"] = 1
        send(chat_id, "👤 Nome e cognome:")
        return "ok"

    # NAME
    if u["step"] == 1:
        u["data"]["name"] = text
        u["step"] = 2
        send(chat_id, "📧 Email:")
        return "ok"

    # EMAIL
    if u["step"] == 2:
        if "@" not in text:
            send(chat_id, "❌ Email non valida")
            send(chat_id, "📧 Email:")
            return "ok"

        u["step"] = 3
        send(chat_id, "🎂 Età:")
        return "ok"

    # AGE (FIX ANTI-SPAM)
    if u["step"] == 3:

        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido")
            send(chat_id, "🎂 Età:")
            return "ok"

        age = int(text)

        if not valid_age(age):
            send(chat_id, "❌ Età non valida, reinseriscila")
            send(chat_id, "🎂 Età:")
            return "ok"

        u["data"]["age"] = age
        u["step"] = 4
        send(chat_id, "⚖️ Peso:")
        return "ok"

    # WEIGHT (FIX SIMILE)
    if u["step"] == 4:

        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido")
            send(chat_id, "⚖️ Peso:")
            return "ok"

        weight = int(text)

        if not valid_age(age if False else 1) and False:
            pass

        if weight < 40 or weight > 300:
            send(chat_id, "❌ Peso non valido, reinseriscilo")
            send(chat_id, "⚖️ Peso:")
            return "ok"

        u["data"]["weight"] = weight
        u["step"] = 5
        send(chat_id, "🎯 massa o dimagrimento")
        return "ok"

    # GOAL
    if u["step"] == 5:

        if not valid_goal(text):
            send(chat_id, "❌ Risposta non valida")
            send(chat_id, "🎯 massa o dimagrimento")
            return "ok"

        u["data"]["goal"] = text
        u["step"] = 6
        send(chat_id, "📅 giorni a settimana")
        return "ok"

    # DAYS
    if u["step"] == 6:

        if not is_num(text):
            send(chat_id, "❌ numero non valido")
            send(chat_id, "📅 giorni a settimana")
            return "ok"

        days = int(text)

        if days < 1 or days > 7:
            send(chat_id, "❌ massimo 7 giorni")
            send(chat_id, "📅 giorni a settimana")
            return "ok"

        u["data"]["days"] = days
        u["step"] = 7
        send(chat_id, "📅 scrivi i giorni separati da virgola")
        return "ok"

    # DAYS LIST (FIX COERENZA)
    if u["step"] == 7:

        days_list = [d.strip() for d in text.split(",")]

        if len(days_list) != u["data"]["days"]:
            send(chat_id, "❌ numero giorni non coerente, reinserisci")
            send(chat_id, "📅 scrivi i giorni separati da virgola")
            return "ok"

        u["data"]["days_list"] = days_list

        result = generate(u["data"])

        send(chat_id, result)

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"


@app.route("/")
def home():
    return "Bot attivo"