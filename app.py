from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_data = {}

# =========================
# SEND
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

# =========================
# DAYS
# =========================
VALID_DAYS = ["lunedi","martedi","mercoledi","giovedi","venerdi","sabato","domenica"]

# =========================
# WORKOUT ENGINE (NO RANDOM)
# =========================

def get_split(goal, days):

    if goal == "massa":

        if days == 1:
            return ["FULL BODY"]

        if days == 2:
            return ["UPPER", "LOWER"]

        if days == 3:
            return ["PUSH", "PULL", "LEGS"]

        if days == 4:
            return ["PUSH", "PULL", "LEGS", "FULL BODY"]

        if days == 5:
            return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER"]

        return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER", "FULL BODY"]

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
# EXERCISE POOLS (COMPLETI)
# =========================

CHEST = [
    "panca piana", "panca inclinata", "push-up", "dip",
    "chest press", "cable fly"
]

BACK = [
    "lat machine", "trazioni", "rematore", "pulley",
    "face pull"
]

LEGS = [
    "squat", "affondi", "leg press", "stacco rumeno",
    "leg curl", "calf raises"
]

SHOULDERS = [
    "shoulder press", "alzate laterali", "arnold press"
]

ARMS = [
    "curl bicipiti", "hammer curl", "pushdown tricipiti", "dip tricipiti"
]

CORE = [
    "plank", "crunch", "leg raise", "ab wheel"
]

CARDIO = [
    "burpees", "squat jump", "jumping jack",
    "mountain climber", "corsa", "corda"
]

# =========================
# WORKOUT BUILDER LOGICO
# =========================

def build(day_type, equipment, focus):

    base = []

    # PUSH
    if day_type == "PUSH":
        base = [CHEST[0], SHOULDERS[0], ARMS[3], SHOULDERS[1]]

    # PULL
    elif day_type == "PULL":
        base = [BACK[0], BACK[2], ARMS[0], BACK[3]]

    # LEGS
    elif day_type == "LEGS":
        base = [LEGS[0], LEGS[1], LEGS[2], LEGS[5]]

    # FULL BODY
    elif day_type == "FULL BODY":
        base = [CHEST[0], BACK[0], LEGS[0], CORE[0]]

    # UPPER
    elif "UPPER" in day_type:
        base = [CHEST[0], BACK[0], SHOULDERS[0], ARMS[0]]

    # LOWER
    elif "LOWER" in day_type:
        base = [LEGS[0], LEGS[2], LEGS[3], LEGS[5]]

    # HIIT
    elif "HIIT" in day_type:
        base = [CARDIO[0], CARDIO[1], CARDIO[3], CORE[0]]

    # CARDIO
    elif "CARDIO" in day_type:
        base = [CARDIO[4], CARDIO[5], CARDIO[2], CORE[0]]

    # CORE
    elif "CORE" in day_type:
        base = CORE

    else:
        base = ["riposo attivo"]

    # ADATTAMENTO ATTREZZATURA
    if equipment == "corpo libero":
        base = [x for x in base if "macchina" not in x]

    return base

# =========================
# GENERATOR
# =========================

def generate(data):

    plan = get_split(data["goal"], data["days"])

    text = f"""
🏋️ PIANO PERSONALIZZATO

👤 {data['name']}
🎯 {data['goal']}
⚖️ {data['weight']} kg
📊 {data['level']}
🏋️ {data['equipment']}
📅 giorni: {data['days']}

"""

    for i in range(data["days"]):

        day_name = data["days_list"][i]
        day_type = plan[i]

        text += f"\n📅 {day_name.upper()} — {day_type}\n"

        exercises = build(day_type, data["equipment"], data["focus"])

        for ex in exercises:
            text += f"- {ex}\n"

        text += "\n-------------------\n"

    return text

# =========================
# WEBHOOK FLOW COMPLETO
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
            return "ok"

        u["step"] = 3
        send(chat_id, "🎂 Età:")
        return "ok"

    # AGE
    if u["step"] == 3:
        if not is_num(text):
            send(chat_id, "❌ Numero non valido")
            return "ok"

        age = int(text)
        if not valid_age(age):
            send(chat_id, "❌ Età non valida")
            return "ok"

        u["data"]["age"] = age
        u["step"] = 4
        send(chat_id, "⚖️ Peso:")
        return "ok"

    # WEIGHT
    if u["step"] == 4:
        if not is_num(text):
            send(chat_id, "❌ Numero non valido")
            return "ok"

        weight = int(text)
        if not valid_weight(weight):
            send(chat_id, "❌ Peso non valido")
            return "ok"

        u["data"]["weight"] = weight
        u["step"] = 5
        send(chat_id, "📊 livello (mai allenato / base / avanzato / esperto)")
        return "ok"

    # LEVEL
    if u["step"] == 5:
        if text not in ["mai allenato","base","avanzato","esperto"]:
            send(chat_id, "❌ livello non valido")
            return "ok"

        u["data"]["level"] = text
        u["step"] = 6
        send(chat_id, "🏋️ attrezzatura (corpo libero / casa / palestra)")
        return "ok"

    # EQUIPMENT
    if u["step"] == 6:
        if text not in ["corpo libero","casa","palestra"]:
            send(chat_id, "❌ attrezzatura non valida")
            return "ok"

        u["data"]["equipment"] = text
        u["step"] = 7
        send(chat_id, "🎯 massa o dimagrimento")
        return "ok"

    # GOAL
    if u["step"] == 7:
        if text not in ["massa","dimagrimento"]:
            send(chat_id, "❌ obiettivo non valido")
            return "ok"

        u["data"]["goal"] = text
        u["step"] = 8
        send(chat_id, "🎯 upper body / lower body / full body")
        return "ok"

    # FOCUS
    if u["step"] == 8:
        if text not in ["upper body","lower body","full body"]:
            send(chat_id, "❌ focus non valido")
            return "ok"

        u["data"]["focus"] = text
        u["step"] = 9
        send(chat_id, "📅 giorni a settimana (1-7)")
        return "ok"

    # DAYS
    if u["step"] == 9:
        if not is_num(text):
            send(chat_id, "❌ numero non valido")
            return "ok"

        days = int(text)
        if days < 1 or days > 7:
            send(chat_id, "❌ max 7 giorni")
            return "ok"

        u["data"]["days"] = days
        u["step"] = 10
        send(chat_id, "📅 scrivi i giorni (lunedi, martedi...)")
        return "ok"

    # DAYS LIST
    if u["step"] == 10:

        raw = text.replace(",", " ")
        days_list = [d.strip() for d in raw.split()]

        for d in days_list:
            if d not in VALID_DAYS:
                send(chat_id, f"❌ giorno non valido: {d}")
                return "ok"

        if len(days_list) != u["data"]["days"]:
            send(chat_id, "❌ numero giorni non coerente")
            return "ok"

        u["data"]["days_list"] = days_list

        result = generate(u["data"])
        send(chat_id, result)

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "Bot attivo"