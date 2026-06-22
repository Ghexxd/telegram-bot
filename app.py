from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "IL_TUO_TOKEN_QUI")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =====================================================================
# CONFIGURAZIONE NOTIFICHE (INSERISCI IL TUO ID PERSONALE QUI)
# =====================================================================
IL_TUO_CHAT_ID = 5734151732  # <--- Sostituisci questo numero con il tuo ID preso da @userinfobot
# =====================================================================

user_data = {}

# =========================
# SEND TELEGRAM
# =========================
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def norm(t):
    t = t.lower().strip()
    replacements = {
        "à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u"
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
def valid_height(h): return 50 <= h <= 300  

VALID_DAYS = [
    "lunedi", "martedi", "mercoledi",
    "giovedi", "venerdi", "sabato", "domenica"
]

# =========================
# LIBRERIE ESERCIZI
# =========================
EX = {
    "PUSH": ["panca piana 4x8-10", "panca inclinata 3x10", "shoulder press 3x10", "alzate laterali 3x12", "dip 3x max"],
    "PULL": ["lat machine 4x10", "rematore 4x10", "curl bicipiti 3x12", "face pull 3x15"],
    "LEGS": ["squat 4x10", "affondi 3x12", "leg press 4x10", "stacco rumeno 3x10", "calf raises 4x15"],
    "UPPER": ["panca 4x10", "lat machine 4x10", "shoulder press 3x10", "curl + tricipiti 3x12"],
    "LOWER": ["squat 4x10", "leg press 4x10", "stacco rumeno 3x10", "calf raises 4x15"],
    "FULL": ["squat 4x10", "panca 4x10", "rematore 4x10", "plank 3x45s"],
    "HIIT": ["burpees 12x", "squat jump 15x", "mountain climber 30s", "jumping jack 1 min"],
    "CARDIO": ["corsa 10-20 min", "corda 5 min", "jumping jack 1 min"],
    "CORE": ["plank 3x45s", "crunch 3x20", "leg raise 3x15", "ab twist 3x30"]
}

EX_BODYWEIGHT = {
    "PUSH": ["push up 4x max", "push up inclinati 3x12", "diamond push up 3x10", "pike push up 3x10"],
    "PULL": ["inverted row sotto tavolo 4x10", "isometric hold schiena 3x30s", "towel curl isometrico 3x12"],
    "LEGS": ["squat a corpo libero 4x15", "affondi 3x12", "wall sit 3x45s", "glute bridge 3x15"],
    "UPPER": ["push up 4x max", "pike push up 3x10", "row improvvisato 3x12", "plank 3x45s"],
    "LOWER": ["squat 4x15", "affondi 3x12", "jump squat 3x12", "wall sit 3x60s"],
    "FULL": ["burpees 4x12", "squat 4x15", "push up 4x max", "plank 3x60s"],
    "HIIT": ["burpees 15x", "jumping jack 1 min", "mountain climber 40s", "squat jump 15x"],
    "CARDIO": ["corsa sul posto 10-20 min", "jumping jack 2 min"],
    "CORE": ["plank 3x45s", "crunch 3x20", "leg raise 3x15", "side plank 3x30s"]
}

EX_HOME = {
    "PUSH": ["floor press con manubri 4x10", "push up 3xmax", "shoulder press manubri 4x10", "alzate laterali manubri 3x12"],
    "PULL": ["trazioni alla sbarra 4xmax", "rematore manubrio 4x10", "curl manubrio 3x12", "shrug manubri 3x15"],
    "LEGS": ["goblet squat 4x12", "affondi con manubri 3x12", "stacco rumeno manubri 4x10", "calf raises 4x20"],
    "UPPER": ["floor press 4x10", "trazioni 4xmax", "shoulder press 4x10", "curl 3x12"],
    "LOWER": ["goblet squat 4x12", "affondi 3x12", "stacco rumeno 4x10", "calf raises 4x20"],
    "FULL": ["goblet squat 4x12", "push up 4xmax", "rematore manubrio 4x10", "plank 3x60s"],
    "HIIT": ["burpees 15x", "jump squat 15x", "mountain climber 40s", "jumping jack 60s"],
    "CARDIO": ["camminata veloce 20 min", "corda 5 min"],
    "CORE": ["plank 3x45s", "crunch 3x20", "leg raise 3x15", "side plank 3x30s"]
}

# =========================
# SPLIT ENGINE
# =========================
def get_split(goal, days):
    if goal == "massa":
        if days == 1: return ["FULL"]
        if days == 2: return ["UPPER", "LOWER"]
        if days == 3: return ["PUSH", "PULL", "LEGS"]
        if days == 4: return ["PUSH", "PULL", "LEGS", "FULL"]
        if days == 5: return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER"]
        return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER", "FULL", "CORE"]
    else:
        if days == 1: return ["HIIT"]
        if days == 2: return ["HIIT", "CARDIO"]
        if days == 3: return ["HIIT", "CORE", "CARDIO"]
        if days == 4: return ["HIIT", "UPPER", "LOWER", "CARDIO"]
        return ["HIIT", "CARDIO", "CORE", "FULL", "HIIT", "CARDIO", "CORE"]

# =========================
# WORKOUT BUILDER
# =========================
def build(day_type, equipment):
    if equipment == "corpo libero":
        return EX_BODYWEIGHT.get(day_type, ["riposo attivo"])
    if equipment == "casa":
        return EX_HOME.get(day_type, ["riposo attivo"])
    return EX.get(day_type, ["riposo attivo"])

# =========================
# GENERATOR
# =========================
def generate(data):
    days = data["days"]
    focus = data["focus"]
    goal = data["goal"]
    
    if goal == "massa":
        if focus == "upper body":
            plans = {
                1: ["UPPER"], 2: ["PUSH", "PULL"], 3: ["PUSH", "PULL", "UPPER"],
                4: ["PUSH", "PULL", "UPPER", "PUSH"], 5: ["PUSH", "PULL", "UPPER", "PUSH", "PULL"],
                6: ["PUSH", "PULL", "UPPER", "PUSH", "PULL", "UPPER"],
                7: ["PUSH", "PULL", "UPPER", "PUSH", "PULL", "UPPER", "PUSH"]
            }
            plan = plans.get(days, ["FULL"])
        elif focus == "lower body":
            plans = {
                1: ["LOWER"], 2: ["LEGS", "LOWER"], 3: ["LEGS", "LOWER", "LEGS"],
                4: ["LEGS", "LOWER", "LEGS", "LOWER"], 5: ["LEGS", "LOWER", "LEGS", "LOWER", "LEGS"],
                6: ["LEGS", "LOWER", "LEGS", "LOWER", "LEGS", "LOWER"],
                7: ["LEGS", "LOWER", "LEGS", "LOWER", "LEGS", "LOWER", "LEGS"]
            }
            plan = plans.get(days, ["FULL"])
        else:
            plan = get_split(goal, days)
    else:
        plan = get_split(goal, days)

    text = f"""
🏋️ PIANO PERSONALIZZATO

👤 {data['name'].title()}
📧 {data['email']}
🎂 {data['age']} anni
📏 {data['height']} cm
⚖️ {data['weight']} kg
📊 Livello: {data['level']}
🏋️ Attrezzatura: {data['equipment']}
🎯 Obiettivo: {data['goal']}
💪 Focus: {data['focus']}
📅 Giorni d'allenamento: {days}
"""

    for i in range(days):
        day = data["days_list"][i]
        type_day = plan[i] if i < len(plan) else "FULL"

        text += f"\n📅 {day.upper()} — {type_day}\n"
        for ex in build(type_day, data["equipment"]):
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
    
    raw_text = msg.get("text", "")
    text = norm(raw_text)

    if chat_id not in user_data:
        user_data[chat_id] = {"step": 0, "data": {}}

    u = user_data[chat_id]

    if text == "/start":
        u["step"] = 1
        u["data"] = {}
        send(chat_id, "👤 Nome e cognome:")
        return "ok"

    if u["step"] == 1:
        u["data"]["name"] = raw_text
        u["step"] = 2
        send(chat_id, "📧 Email:")
        return "ok"

    if u["step"] == 2:
        if "@" not in text:
            send(chat_id, "❌ Email non valida. Reinserisci:")
            return "ok"
        u["data"]["email"] = text
        u["step"] = 3
        send(chat_id, "🎂 Età:")
        return "ok"

    if u["step"] == 3:
        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido per l'età:")
            return "ok"
        age = int(text)
        if not valid_age(age):
            send(chat_id, "❌ Età non consentita (inserire tra 10 e 99):")
            return "ok"
        u["data"]["age"] = age
        u["step"] = 35  
        send(chat_id, "📏 Altezza (in cm, es: 175):")
        return "ok"

    if u["step"] == 35:  
        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido per l'altezza:")
            return "ok"
        height = int(text)
        if not valid_height(height):
            send(chat_id, "❌ Altezza non valida (inserire tra 50 e 300 cm):")  
            return "ok"
        u["data"]["height"] = height
        u["step"] = 4
        send(chat_id, "⚖️ Peso (in kg, es: 70):")
        return "ok"

    if u["step"] == 4:
        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido per il peso:")
            return "ok"
        weight = int(text)
        if not valid_weight(weight):
            send(chat_id, "❌ Peso fuori dai limiti (40-300 kg):")
            return "ok"
        u["data"]["weight"] = weight
        u["step"] = 5
        send(chat_id, "📊 Seleziona il tuo livello d'esperienza:\n- mai allenato\n- livello base\n- livello avanzato\n- esperto")
        return "ok"

    if u["step"] == 5:
        if text not in ["mai allenato", "livello base", "livello avanzato", "esperto"]:
            send(chat_id, "❌ Livello non valido. Scegli tra quelli in elenco:")
            return "ok"
        u["data"]["level"] = text
        u["step"] = 6
        send(chat_id, "🏋️ Scegli l'attrezzatura:\n- corpo libero\n- casa\n- palestra")
        return "ok"

    if u["step"] == 6:
        if text not in ["corpo libero", "casa", "palestra"]:
            send(chat_id, "❌ Attrezzatura non valida. Scegli tra corpo libero, casa o palestra:")
            return "ok"
        u["data"]["equipment"] = text
            
        u["step"] = 7
        send(chat_id, "🎯 Qual è il tuo obiettivo?\n- massa\n- dimagrimento")
        return "ok"

    if u["step"] == 7:
        if text not in ["massa", "dimagrimento"]:
            send(chat_id, "❌ Obiettivo non valido. Scegli tra massa o dimagrimento:")
            return "ok"
        u["data"]["goal"] = text
        u["step"] = 8
        send(chat_id, "💪 Scegli il focus muscolare:\n- upper body\n- lower body\n- full body")
        return "ok"

    if u["step"] == 8:
        if text not in ["upper body", "lower body", "full body"]:
            send(chat_id, "❌ Focus non valido. Scegli tra upper body, lower body o full body:")
            return "ok"
        u["data"]["focus"] = text
        u["step"] = 9
        send(chat_id, "📅 Quanti giorni a settimana vuoi allenarti? (1-7):")
        return "ok"

    if u["step"] == 9:
        if not is_num(text):
            send(chat_id, "❌ Inserisci un numero valido da 1 a 7:")
            return "ok"
        days = int(text)
        if days < 1 or days > 7:
            send(chat_id, "❌ Puoi scegliere solo da 1 a 7 giorni:")
            return "ok"
        u["data"]["days"] = days

        if days == 1:
            send(chat_id, "⚠️ Nota: 1 giorno è poco per risultati ottimali.")
            u["data"]["days_list"] = ["allenamento"] 
            result = generate(u["data"])
            
            # Mandiamo la risposta all'utente
            send(chat_id, result)
            # Mandiamo la notifica a TE (con i dati dell'utente)
            send(IL_TUO_CHAT_ID, f"🔔 NUOVO LEAD RICEVUTO:\n{result}")
            
            user_data[chat_id] = {"step": 0, "data": {}}
            return "ok"
            
        elif days == 7:
            u["data"]["days_list"] = VALID_DAYS 
            result = generate(u["data"])
            
            # Mandiamo la risposta all'utente
            send(chat_id, result)
            # Mandiamo la notifica a TE (con i dati dell'utente)
            send(IL_TUO_CHAT_ID, f"🔔 NUOVO LEAD RICEVUTO:\n{result}")
            
            user_data[chat_id] = {"step": 0, "data": {}}
            return "ok"

        u["step"] = 10
        send(chat_id, f"📅 Elenca {days} giorni separati da uno spazio o virgola (es: lunedi, mercoledi...):")
        return "ok"

    if u["step"] == 10:
        raw = text.replace(",", " ")
        days_list = raw.split()

        for d in days_list:
            if d not in VALID_DAYS:
                send(chat_id, f"❌ Giorno non riconosciuto: '{d}'. Riprova a elencarli tutti:")
                return "ok"

        if len(days_list) != u["data"]["days"]:
            send(chat_id, f"❌ Avevi selezionato {u['data']['days']} giorni, ma ne hai elencati {len(days_list)}. Riprova:")
            return "ok"

        u["data"]["days_list"] = days_list
        result = generate(u["data"])
        
        # Mandiamo la risposta all'utente
        send(chat_id, result)
        # Mandiamo la notifica a TE (con i dati dell'utente)
        send(IL_TUO_CHAT_ID, f"🔔 NUOVO LEAD RICEVUTO:\n{result}")

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot attivo"