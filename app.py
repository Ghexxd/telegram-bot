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
    t = t.lower().strip()

    replacements = {
        "à": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u"
    }

    for old, new in replacements.items():
        t = t.replace(old, new)

    return t

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
VALID_DAYS = [
    "lunedi","martedi","mercoledi",
    "giovedi","venerdi","sabato","domenica"
]

# =========================
# EXERCISE LIBRARY (PALESTRA)
# =========================
EX = {

"PUSH": [
    "panca piana 4x8-10",
    "panca inclinata 3x10",
    "shoulder press 3x10",
    "alzate laterali 3x12",
    "dip 3x max"
],

"PULL": [
    "lat machine 4x10",
    "rematore 4x10",
    "curl bicipiti 3x12",
    "face pull 3x15"
],

"LEGS": [
    "squat 4x10",
    "affondi 3x12",
    "leg press 4x10",
    "stacco rumeno 3x10",
    "calf raises 4x15"
],

"UPPER": [
    "panca 4x10",
    "lat machine 4x10",
    "shoulder press 3x10",
    "curl + tricipiti 3x12"
],

"LOWER": [
    "squat 4x10",
    "leg press 4x10",
    "stacco rumeno 3x10",
    "calf raises 4x15"
],

"FULL": [
    "squat 4x10",
    "panca 4x10",
    "rematore 4x10",
    "plank 3x45s"
],

"HIIT": [
    "burpees 12x",
    "squat jump 15x",
    "mountain climber 30s",
    "jumping jack 1 min"
],

"CARDIO": [
    "corsa 10-20 min",
    "corda 5 min",
    "jumping jack 1 min"
],

"CORE": [
    "plank",
    "crunch",
    "leg raise",
    "ab twist"
]

}

# =========================
# EXERCISE LIBRARY (CORPO LIBERO)
# =========================
EX_BODYWEIGHT = {

"PUSH": [
    "push up 4x max",
    "push up inclinati 3x12",
    "diamond push up 3x10",
    "pike push up 3x10"
],

"PULL": [
    "inverted row sotto tavolo 4x10",
    "isometric hold schiena 3x30s",
    "towel curl isometrico 3x12"
],

"LEGS": [
    "squat a corpo libero 4x15",
    "affondi 3x12",
    "wall sit 3x45s",
    "glute bridge 3x15"
],

"UPPER": [
    "push up 4x max",
    "pike push up 3x10",
    "row improvvisato 3x12",
    "plank 3x45s"
],

"LOWER": [
    "squat 4x15",
    "affondi 3x12",
    "jump squat 3x12",
    "wall sit 3x60s"
],

"FULL": [
    "burpees 4x12",
    "squat 4x15",
    "push up 4x max",
    "plank 3x60s"
],

"HIIT": [
    "burpees 15x",
    "jumping jack 1 min",
    "mountain climber 40s",
    "squat jump 15x"
],

"CARDIO": [
    "corsa sul posto 10-20 min",
    "jumping jack 2 min"
],

"CORE": [
    "plank",
    "crunch",
    "leg raise",
    "side plank"
]

}

EX_HOME = {

"PUSH": [
    "floor press con manubri 4x10",
    "push up 3xmax",
    "shoulder press manubri 4x10",
    "alzate laterali manubri 3x12"
],

"PULL": [
    "trazioni alla sbarra 4xmax",
    "rematore manubrio 4x10",
    "curl manubrio 3x12",
    "shrug manubri 3x15"
],

"LEGS": [
    "goblet squat 4x12",
    "affondi con manubri 3x12",
    "stacco rumeno manubri 4x10",
    "calf raises 4x20"
],

"UPPER": [
    "floor press 4x10",
    "trazioni 4xmax",
    "shoulder press 4x10",
    "curl 3x12"
],

"LOWER": [
    "goblet squat 4x12",
    "affondi 3x12",
    "stacco rumeno 4x10",
    "calf raises 4x20"
],

"FULL": [
    "goblet squat 4x12",
    "push up 4xmax",
    "rematore manubrio 4x10",
    "plank 3x60s"
],

"HIIT": [
    "burpees 15x",
    "jump squat 15x",
    "mountain climber 40s",
    "jumping jack 60s"
],

"CARDIO": [
    "camminata veloce 20 min",
    "corda 5 min"
],

"CORE": [
    "plank",
    "crunch",
    "leg raise",
    "side plank"
]

}


# =========================
# SPLIT ENGINE
# =========================
def get_split(goal, days):

    if goal == "massa":

        if days == 1:
            return ["FULL"]
        if days == 2:
            return ["UPPER", "LOWER"]
        if days == 3:
            return ["PUSH", "PULL", "LEGS"]
        if days == 4:
            return ["PUSH", "PULL", "LEGS", "FULL"]
        if days == 5:
            return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER"]
        return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER", "FULL"]

    else:

        if days == 1:
            return ["HIIT"]
        if days == 2:
            return ["HIIT", "CARDIO"]
        if days == 3:
            return ["HIIT", "CORE", "CARDIO"]
        if days == 4:
            return ["HIIT", "UPPER", "LOWER", "CARDIO"]
        return ["HIIT", "CARDIO", "CORE", "FULL"]

# =========================
# WORKOUT BUILDER (MODIFICATO)
# =========================
def build(day_type, equipment):

    if equipment == "corpo libero":
        return EX_BODYWEIGHT.get(day_type, ["riposo attivo"])

    if equipment == "casa":
        return EX_HOME.get(day_type, ["riposo attivo"])

    return EX.get(day_type, ["riposo attivo"])


def get_multiplier(age, level):

    multiplier = 1

    if age < 18:
        multiplier = 0.8
    elif age <= 35:
        multiplier = 1.2
    elif age <= 60:
        multiplier = 1
    else:
        multiplier = 0.7

    if level == "mai allenato":
        multiplier *= 0.8

    elif level == "livello base":
        multiplier *= 1

    elif level == "livello avanzato":
        multiplier *= 1.2

    elif level == "esperto":
        multiplier *= 1.4

    return multiplier

# =========================
# GENERATOR
# =========================
def generate(data):

    plan = get_split(data["goal"], data["days"])

    focus = data["focus"]

    if focus == "upper body" and data["days"] >= 3:
        plan = ["PUSH", "PULL", "UPPER"] + plan[3:]

    elif focus == "lower body" and data["days"] >= 3:
        plan = ["LEGS", "LOWER", "LEGS"] + plan[3:]

    text = f"""
🏋️ PIANO PERSONALIZZATO

👤 {data['name']}
📧 {data['email']}
🎂 {data['age']}
⚖️ {data['weight']} kg
📊 livello esperienza: {data['level']}
🏋️ attrezzatura: {data['equipment']}
🎯 obiettivo: {data['goal']}
💪 focus: {data['focus']}
📅 giorni: {data['days']}
"""

    for i in range(data["days"]):

        day = data["days_list"][i]
        type_day = plan[i]

        text += f"\n📅 {day.upper()} — {type_day}\n"

        for ex in build(type_day, data["equipment"]):
            text += f"- {ex}\n"

        text += "\n-------------------\n"

    return text

# =========================
# WEBHOOK (IDENTICO AL TUO)
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

    if text == "/start":
        u["step"] = 1
        send(chat_id, "👤 Nome e cognome:")
        return "ok"

    if u["step"] == 1:
        u["data"]["name"] = text
        u["step"] = 2
        send(chat_id, "📧 Email:")
        return "ok"

    if u["step"] == 2:
        if "@" not in text:
            send(chat_id, "❌ Email non valida")
            return "ok"

        u["data"]["email"] = text
        u["step"] = 3
        send(chat_id, "🎂 Età:")
        return "ok"

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
        send(chat_id,
             "📊 livello esperienza:\n"
             "- mai allenato\n"
             "- livello base\n"
             "- livello avanzato\n"
             "- esperto")
        return "ok"

    if u["step"] == 5:
        if text not in ["mai allenato","livello base","livello avanzato","esperto"]:
            send(chat_id, "❌ livello non valido")
            return "ok"

        u["data"]["level"] = text
        u["step"] = 6
        send(chat_id, "🏋️ attrezzatura (corpo libero / casa / palestra)")
        return "ok"

    if u["step"] == 6:
        if text not in ["corpo libero","casa","palestra"]:
            send(chat_id, "❌ attrezzatura non valida")
            return "ok"

        u["data"]["equipment"] = text
        u["step"] = 7
        send(chat_id, "🎯 massa o dimagrimento")
        return "ok"

    if u["step"] == 7:
        if text not in ["massa","dimagrimento"]:
            send(chat_id, "❌ obiettivo non valido")
            return "ok"

        u["data"]["goal"] = text
        u["step"] = 8
        send(chat_id, "💪 focus (upper body / lower body / full body)")
        return "ok"

    if u["step"] == 8:
        if text not in ["upper body","lower body","full body"]:
            send(chat_id, "❌ focus non valido")
            return "ok"

        u["data"]["focus"] = text
        u["step"] = 9
        send(chat_id, "📅 giorni a settimana (1-7)")
        return "ok"

    if u["step"] == 9:
        if not is_num(text):
            send(chat_id, "❌ numero non valido")
            return "ok"

        days = int(text)

        if days < 1 or days > 7:
            send(chat_id, "❌ max 7 giorni")
            return "ok"

        u["data"]["days"] = days

        if days == 1:
            send(chat_id, "⚠️ 1 giorno è poco per risultati ottimali.")

        u["step"] = 10
        send(chat_id, "📅 scrivi i giorni (lunedi, martedi...)")
        return "ok"

    if u["step"] == 10:

        raw = text.replace(",", " ")
        days_list = raw.split()

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