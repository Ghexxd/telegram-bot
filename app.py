from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "IL_TUO_TOKEN_QUI")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =====================================================================
# CONFIGURAZIONE NOTIFICHE (IL TUO ID PERSONALE)
# =====================================================================
IL_TUO_CHAT_ID = 5734151732  

user_data = {}

# =========================
# SEND TELEGRAM (HTML ABILITATO)
# =========================
def send(chat_id, text):
    requests.post(f"{URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"  # <--- Permette di vedere i link cliccabili e i grassetti
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

# =====================================================================
# LIBRERIE ESERCIZI
# =====================================================================
EX = {
    "PUSH": [("panca piana", "[F]"), ("panca inclinata", "[C]"), ("shoulder press", "[F]"), ("alzate laterali", "[C]"), ("dip", "[F]")],
    "PULL": [("lat machine", "[F]"), ("rematore bilanciere", "[F]"), ("curl bicipiti", "[C]"), ("face pull", "[C]")],
    "LEGS": [("squat bilanciere", "[F]"), ("affondi manubri", "[C]"), ("leg press", "[F]"), ("stacco rumeno", "[F]"), ("calf raises", "[C]")],
    "UPPER": [("panca piana", "[F]"), ("lat machine", "[F]"), ("shoulder press", "[F]"), ("curl + tricipiti", "[C]")],
    "LOWER": [("squat bilanciere", "[F]"), ("leg press", "[F]"), ("stacco rumeno", "[F]"), ("calf raises", "[C]")],
    "FULL": [("squat bilanciere", "[F]"), ("panca piana", "[F]"), ("rematore bilanciere", "[F]"), ("plank", "[T]")],
    "HIIT": [("burpees", "[T]"), ("squat jump", "[T]"), ("mountain climber", "[T]"), ("jumping jack", "[T]")],
    "CARDIO": [("corsa tapis roulant", "[T]"), ("corda", "[T]"), ("jumping jack", "[T]")],
    "CORE": [("plank", "[T]"), ("crunch", "[C]"), ("leg raise", "[C]"), ("ab twist", "[C]")],
    "RECOMP_FULL": [("squat bilanciere", "[F]"), ("panca piana", "[F]"), ("rematore bilanciere", "[F]"), ("affondi", "[C]"), ("circuito core", "[T]")],
    "RECOMP_UPPER": [("panca inclinata", "[F]"), ("trazioni o lat machine", "[F]"), ("military press", "[F]"), ("curl manubri + dip", "[C]"), ("hiit tapis roulant", "[T]")],
    "RECOMP_LOWER": [("squat bilanciere", "[F]"), ("stacco rumeno", "[F]"), ("leg press", "[C]"), ("calf raises", "[C]"), ("crunch inverso", "[C]")]
}

EX_BODYWEIGHT = {
    "PUSH": [("push up", "[F]"), ("push up inclinati", "[C]"), ("diamond push up", "[C]"), ("pike push up", "[F]")],
    "PULL": [("inverted row sotto tavolo", "[F]"), ("isometric hold schiena", "[T]"), ("towel curl isometrico", "[C]")],
    "LEGS": [("squat a corpo libero", "[F]"), ("affondi", "[C]"), ("wall sit", "[T]"), ("glute bridge", "[C]")],
    "UPPER": [("push up", "[F]"), ("pike push up", "[F]"), ("row improvvisato", "[C]"), ("plank", "[T]")],
    "LOWER": [("squat a corpo libero", "[F]"), ("affondi", "[C]"), ("jump squat", "[T]"), ("wall sit", "[T]")],
    "FULL": [("burpees", "[T]"), ("squat a corpo libero", "[F]"), ("push up", "[F]"), ("plank", "[T]")],
    "HIIT": [("burpees", "[T]"), ("jumping jack", "[T]"), ("mountain climber", "[T]"), ("squat jump", "[T]")],
    "CARDIO": [("corsa sul posto", "[T]"), ("jumping jack", "[T]")],
    "CORE": [("plank", "[T]"), ("crunch", "[C]"), ("leg raise", "[C]"), ("side plank", "[T]")],
    "RECOMP_FULL": [("squat jump", "[T]"), ("push up", "[F]"), ("inverted row", "[F]"), ("affondi alternati", "[C]"), ("burpees", "[T]")],
    "RECOMP_UPPER": [("push up", "[F]"), ("pike push up", "[F]"), ("row sotto il tavolo", "[F]"), ("plank up", "[C]"), ("jumping jack", "[T]")],
    "RECOMP_LOWER": [("squat a corpo libero", "[F]"), ("affondi", "[C]"), ("glute bridge a 1 gamba", "[C]"), ("wall sit", "[T]"), ("mountain climber", "[T]")]
}

EX_HOME = {
    "PUSH": [("floor press con manubri", "[F]"), ("push up", "[F]"), ("shoulder press manubri", "[F]"), ("alzate laterali manubri", "[C]")],
    "PULL": [("trazioni alla sbarra", "[F]"), ("rematore manubrio", "[F]"), ("curl manubrio", "[C]"), ("shrug manubri", "[C]")],
    "LEGS": [("goblet squat", "[F]"), ("affondi con manubri", "[C]"), ("stacco rumeno manubri", "[F]"), ("calf raises", "[C]")],
    "UPPER": [("floor press manubri", "[F]"), ("trazioni", "[F]"), ("shoulder press manubri", "[F]"), ("curl manubrio", "[C]")],
    "LOWER": [("goblet squat", "[F]"), ("affondi con manubri", "[C]"), ("stacco rumeno manubri", "[F]"), ("calf raises", "[C]")],
    "FULL": [("goblet squat", "[F]"), ("push up", "[F]"), ("rematore manubrio", "[F]"), ("plank", "[T]")],
    "HIIT": [("burpees", "[T]"), ("jump squat", "[T]"), ("mountain climber", "[T]"), ("jumping jack", "[T]")],
    "CARDIO": [("camminata veloce", "[T]"), ("corda", "[T]")],
    "CORE": [("plank", "[T]"), ("crunch", "[C]"), ("leg raise", "[C]"), ("side plank", "[T]")],
    "RECOMP_FULL": [("goblet squat", "[F]"), ("floor press manubri", "[F]"), ("rematore manubri", "[F]"), ("affondi manubri", "[C]"), ("squat jump", "[T]")],
    "RECOMP_UPPER": [("panca inclinata manubri", "[F]"), ("rematore a un braccio", "[F]"), ("shoulder press manubri", "[F]"), ("curl + tricipiti manubri", "[C]"), ("jumping jack", "[T]")],
    "RECOMP_LOWER": [("goblet squat", "[F]"), ("stacco rumeno manubri", "[F]"), ("affondi camminati", "[C]"), ("calf raises manubri", "[C]"), ("plank", "[T]")]
}

# =====================================================================
# VOLUME ENGINE
# =====================================================================
def get_volume_string(ex_info, level):
    ex_name, ex_type = ex_info
    
    if level == "mai allenato":
        if ex_type == "[F]": return f"{ex_name} 2x8 (Focus tecnica, buffer alto)"
        if ex_type == "[C]": return f"{ex_name} 2x10 (Carico leggero)"
        return f"{ex_name} 2x30s (Ritmo blando)"

    elif level == "livello base":
        if ex_type == "[F]": return f"{ex_name} 3x8"
        if ex_type == "[C]": return f"{ex_name} 3x10"
        return f"{ex_name} 3x45s"

    elif level == "livello avanzato":
        if ex_type == "[F]": return f"{ex_name} 4x8"
        if ex_type == "[C]": return f"{ex_name} 3x12"
        return f"{ex_name} 4x45s"

    elif level == "esperto":
        if ex_type == "[F]": return f"{ex_name} 4x6 (Alta intensità di carico)"
        if ex_type == "[C]": return f"{ex_name} 4x12 (Focus pompaggio muscolare)"
        return f"{ex_name} 4x60s (Massima intensità)"

    return f"{ex_name} 3x10"

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
    elif goal == "ricomposizione corporea":
        if days == 1: return ["RECOMP_FULL"]
        if days == 2: return ["RECOMP_UPPER", "RECOMP_LOWER"]
        if days == 3: return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL"]
        if days == 4: return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_UPPER", "RECOMP_LOWER"]
        if days == 5: return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL"]
        return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL", "CORE", "HIIT"]
    else:
        if days == 1: return ["HIIT"]
        if days == 2: return ["HIIT", "CARDIO"]
        if days == 3: return ["HIIT", "CORE", "CARDIO"]
        if days == 4: return ["HIIT", "UPPER", "LOWER", "CARDIO"]
        return ["HIIT", "CARDIO", "CORE", "FULL", "HIIT", "CARDIO", "CORE"]

# =========================
# WORKOUT BUILDER
# =========================
def build(day_type, equipment, level):
    if equipment == "corpo libero":
        raw_exercises = EX_BODYWEIGHT.get(day_type, [])
    elif equipment == "casa":
        raw_exercises = EX_HOME.get(day_type, [])
    else:
        raw_exercises = EX.get(day_type, [])

    if not raw_exercises:
        return ["riposo attivo"]

    return [get_volume_string(ex, level) for ex in raw_exercises]

# =====================================================================
# GENERATOR (CON PUBBLICITÀ A @GymMethod2026Shop IN CIMA)
# =====================================================================
def generate(data):
    days = data["days"]
    focus = data["focus"]
    goal = data["goal"]
    level = data["level"]
    
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
    elif goal == "ricomposizione corporea":
        if focus == "upper body":
            plan = ["RECOMP_UPPER" if x % 2 == 0 else "RECOMP_FULL" for x in range(days)]
        elif focus == "lower body":
            plan = ["RECOMP_LOWER" if x % 2 == 0 else "RECOMP_FULL" for x in range(days)]
        else:
            plan = get_split(goal, days)
    else:
        plan = get_split(goal, days)

    # Box pubblicitario iniziale
    text = """🔥 <b>INTEGRATORI E ATTREZZATURA SCONTATI?</b> 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━
Prima di scoprire la tua scheda, entra nel nostro <b>Canale Telegram Ufficiale</b> @GymMethod2026Shop dove scoviamo ogni giorno i migliori sconti Amazon su <i>creatina, proteine e attrezzi per la tua Home Gym!</i>

👉 <a href="https://t.me/GymMethod2026Shop">CLICCA QUI PER ENTRARE NEL CANALE SHOP</a> 👈
━━━━━━━━━━━━━━━━━━━━━━━━━━

🏋️ <b>IL TUO PIANO PERSONALIZZATO</b>

👤 <b>Nome:</b> {name}
📧 <b>Email:</b> {email}
🎂 <b>Età:</b> {age} anni
📏 <b>Altezza:</b> {height} cm
⚖️ <b>Peso:</b> {weight} kg
📊 <b>Livello:</b> {level}
🏋️ <b>Attrezzatura:</b> {equipment}
🎯 <b>Obiettivo:</b> {goal}
💪 <b>Focus:</b> {focus}
📅 <b>Giorni d'allenamento:</b> {days}
""".format(
        name=data['name'].title(),
        email=data['email'],
        age=data['age'],
        height=data['height'],
        weight=data['weight'],
        level=data['level'].upper(),
        equipment=data['equipment'].title(),
        goal=data['goal'].title(),
        focus=data['focus'].title(),
        days=days
    )

    for i in range(days):
        day = data["days_list"][i]
        type_day = plan[i] if i < len(plan) else "FULL"

        text += f"\n📅 <b>{day.upper()} — {type_day}</b>\n"
        for ex in build(type_day, data["equipment"], level):
            text += f"- {ex}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    text += "\n⚠️ <i>Questa scheda NON sostituisce il parere di un medico! Seguila soltanto se sei perfettamente in salute.</i>\n"

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
        send(chat_id, "🎯 Qual è il tuo obiettivo?\n- massa\n- dimagrimento\n- ricomposizione corporea (entrambi)")
        return "ok"

    if u["step"] == 7:
        if text in ["ricomposizione corporea", "entrambi", "ricomposizione"]:
            u["data"]["goal"] = "ricomposizione corporea"
        elif text in ["massa", "dimagrimento"]:
            u["data"]["goal"] = text
        else:
            send(chat_id, "❌ Obiettivo non valido. Scegli tra massa, dimagrimento o ricomposizione corporea:")
            return "ok"
            
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
            
            send(chat_id, result)
            send(IL_TUO_CHAT_ID, f"🔔 NUOVO LEAD RICEVUTO:\n{result}")
            
            user_data[chat_id] = {"step": 0, "data": {}}
            return "ok"
            
        elif days == 7:
            u["data"]["days_list"] = VALID_DAYS 
            result = generate(u["data"])
            
            send(chat_id, result)
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
        
        send(chat_id, result)
        send(IL_TUO_CHAT_ID, f"🔔 NUOVO LEAD RICEVUTO:\n{result}")

        user_data[chat_id] = {"step": 0, "data": {}}
        return "ok"

    return "ok"

@app.route("/")
def home():
    return "Bot attivo e pubblicità impostata su @GymMethod2026Shop"