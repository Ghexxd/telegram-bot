from flask import Flask, request
import requests
import os
import random

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

user_data = {}

# -------------------------
# SEND
# -------------------------
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def norm(t):
    return t.lower().strip()

def is_num(x):
    return x.isdigit()

# -------------------------
# LIBRERIA ESERCIZI (BASE)
# -------------------------
MASSA = {
    "push_a": ["panca 4x10", "shoulder press 3x10", "dip 3x max", "alzate laterali 3x12"],
    "push_b": ["panca inclinata 4x8", "push-up 4x max", "arnold press 3x10", "tricipiti 3x12"],
    "push_c": ["chest press 4x10", "push-up lento 4x8", "shoulder press 4x10", "dip 3x max"],

    "pull_a": ["rematore 4x10", "lat machine 4x10", "curl 3x12", "pullover 3x12"],
    "pull_b": ["trazioni 4x max", "rematore bilanciere 4x8", "curl hammer 3x12", "rear delts 3x12"],
    "pull_c": ["lat machine stretta 4x10", "pulley 4x10", "curl concentrato 3x12", "face pull 3x15"],

    "legs_a": ["squat 4x10", "affondi 3x12", "leg press 4x10", "calf raises 4x15"],
    "legs_b": ["stacco rumeno 4x8", "leg curl 3x12", "squat lento 4x10", "glute bridge 3x15"],
    "legs_c": ["hack squat 4x10", "affondi camminati 3x12", "leg extension 3x12", "calf 4x20"],

    "full_a": ["squat 4x10", "panca 4x10", "rematore 4x10", "plank 3x40s"],
    "full_b": ["squat jump", "push-up max", "affondi 3x12", "addome 3x15"],
    "full_c": ["leg press 4x10", "lat machine 4x10", "dip 3x max", "core 3x"],
    "full_d": ["circuito completo 4 giri", "burpees", "squat", "push-up"]
}

DIMAGRIMENTO = {
    "hiit_a": ["burpees 12x", "squat jump 15x", "push-up 12x", "mountain climber 30s"],
    "hiit_b": ["jumping jack 1 min", "burpees 10x", "plank 45s", "corsa 2 min"],
    "hiit_c": ["tabata burpees", "squat 20x", "push-up 15x", "plank 1 min"],
    "hiit_d": ["circuito 5 giri", "jump squat", "mountain climber", "addome"]
}

# -------------------------
# ENGINE
# -------------------------
def build_day(goal, level, focus):

    if goal == "massa":

        if level == "mai allenato":
            pool = ["full_a", "full_b"]

        elif level == "base":

            if focus == "push":
                pool = ["push_a", "push_b", "push_c"]
            elif focus == "pull":
                pool = ["pull_a", "pull_b", "pull_c"]
            elif focus == "legs":
                pool = ["legs_a", "legs_b", "legs_c"]
            else:
                pool = ["full_a", "full_b", "full_c", "full_d"]

        else:
            pool = list(MASSA.keys())

        chosen = random.choice(pool)
        return "\n".join(MASSA[chosen])

    else:

        if level == "mai allenato":
            pool = ["hiit_a", "hiit_b"]

        elif level == "base":
            pool = ["hiit_a", "hiit_b", "hiit_c"]

        else:
            pool = list(DIMAGRIMENTO.keys())

        chosen = random.choice(pool)
        return "\n".join(DIMAGRIMENTO[chosen])

# -------------------------
# WORKOUT GENERATOR
# -------------------------
def generate(data):

    name = data["name"]
    age = int(data["age"])
    weight = int(data["weight"])
    level = data["level"]
    goal = data["goal"]
    focus = data["focus"]
    days = data["days"]
    days_list = data["days_list"]

    intensity = "ottimale"
    if age < 18:
        intensity = "giovane"
    elif age > 35:
        intensity = "protetto"

    text = f"""
🏋️ PIANO PERSONALIZZATO

👤 {name}
🎯 {goal}
📊 {level}
🔥 {intensity}
⚖️ {weight} kg

"""

    for i in range(days):

        day = days_list[i] if i < len(days_list) else f"Giorno {i+1}"

        text += f"\n📅 {day.upper()}\n"
        text += build_day(goal, level, focus)
        text += "\n-----------------\n"

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
        u["step"] = 3
        send(chat_id, "🎂 Età:")
        return "ok"

    if u["step"] == 3:
        if not is_num(text):
            send(chat_id, "❌ Numero valido")
            return "ok"
        u["data"]["age"] = text
        u["step"] = 4
        send(chat_id, "⚖️ Peso:")
        return "ok"

    if u["step"] == 4:
        if not is_num(text):
            send(chat_id, "❌ Numero valido")
            return "ok"
        u["data"]["weight"] = text
        u["step"] = 5
        send(chat_id, "📊 livello (mai allenato/base/avanzato/esperto)")
        return "ok"

    if u["step"] == 5:
        u["data"]["level"] = text
        u["step"] = 6
        send(chat_id, "🎯 massa o dimagrimento?")
        return "ok"

    if u["step"] == 6:
        u["data"]["goal"] = text
        u["step"] = 7
        send(chat_id, "🎯 focus (push/pull/legs/full body)")
        return "ok"

    if u["step"] == 7:
        u["data"]["focus"] = text
        u["step"] = 8
        send(chat_id, "📅 giorni a settimana (1-7)")
        return "ok"

    if u["step"] == 8:
        if not is_num(text):
            send(chat_id, "❌ numero valido")
            return "ok"
        days = int(text)
        if days < 1 or days > 7:
            send(chat_id, "❌ 1-7 giorni")
            return "ok"

        u["data"]["days"] = days
        u["step"] = 9
        send(chat_id, "📅 scrivi giorni separati da virgola")
        return "ok"

    if u["step"] == 9:

        u["data"]["days_list"] = [d.strip() for d in text.split(",")]

        result = generate(u["data"])

        send(chat_id, result)

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot attivo"