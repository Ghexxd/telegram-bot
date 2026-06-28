from flask import Flask, request
import requests
import os
import re

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "IL_TUO_TOKEN_QUI")
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =====================================================================
# CONFIGURAZIONE NOTIFICHE (IL TUO ID PERSONALE)
# =====================================================================
IL_TUO_CHAT_ID = 5734151732  

user_data = {}

# =========================
# SEND TELEGRAM
# =========================
def send(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        requests.post(f"{URL}/sendMessage", json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio del messaggio: {e}")

def norm(t):
    if not t:
        return ""
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

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def valid_weight(w): return 40 <= w <= 300
def valid_height(h): return 50 <= h <= 300  

VALID_DAYS = [
    "lunedi", "martedi", "mercoledi",
    "giovedi", "venerdi", "sabato", "domenica"
]

# =====================================================================
# LIBRERIE ESERCIZI AMPLIATE
# =====================================================================
EX = {
    "PUSH": [("panca piana bilanciere", "[F]"), ("panca inclinata manubri", "[C]"), ("military press", "[F]"), ("dip alle parallele", "[F]"), ("alzate laterali cavi", "[C]"), ("pushdown tricipiti", "[C]")],
    "PULL": [("trazioni alla sbarra", "[F]"), ("lat machine avanti", "[F]"), ("rematore bilanciere", "[F]"), ("pulley basso", "[C]"), ("curl bicipiti bilanciere", "[C]"), ("face pull cavi", "[C]")],
    "LEGS": [("squat bilanciere", "[F]"), ("stacco da terra", "[F]"), ("leg press 45°", "[F]"), ("leg curl", "[C]"), ("affondi camminati", "[C]"), ("calf raises seduto", "[C]")],
    "UPPER": [("panca piana bilanciere", "[F]"), ("trazioni alla sbarra", "[F]"), ("shoulder press manubri", "[F]"), ("rematore manubrio", "[F]"), ("curl bicipiti + kickback tricipiti", "[C]")],
    "LOWER": [("squat bilanciere", "[F]"), ("stacco rumeno", "[F]"), ("leg extension", "[C]"), ("leg curl sdraiato", "[C]"), ("calf raises in piedi", "[C]")],
    "FULL": [("squat bilanciere", "[F]"), ("panca piana", "[F]"), ("trazioni o lat machine", "[F]"), ("military press", "[F]"), ("plank addome", "[T]")],
    "HIIT": [("burpees", "[T]"), ("squat jump", "[T]"), ("mountain climber", "[T]"), ("jumping jack", "[T]"), ("thruster con manubri", "[T]")],
    "CARDIO": [("corsa tapis roulant", "[T]"), ("ellittica o cyclette", "[T]"), ("corda", "[T]"), ("jumping jack", "[T]")],
    "CORE": [("plank frontale", "[T]"), ("crunch inverso", "[C]"), ("leg raise alla sbarra", "[C]"), ("ab wheel rollout", "[C]"), ("russian twist", "[C]")],
    "RECOMP_FULL": [("squat bilanciere", "[F]"), ("panca piana", "[F]"), ("rematore manubri", "[F]"), ("affondi bulgari", "[C]"), ("circuito core intensive", "[T]")],
    "RECOMP_UPPER": [("panca inclinata", "[F]"), ("lat machine stretto", "[F]"), ("military press", "[F]"), ("alzate laterali + alzate 90°", "[C]"), ("hiit tapis roulant", "[T]")],
    "RECOMP_LOWER": [("squat bilanciere", "[F]"), ("stacco rumeno bilanciere", "[F]"), ("leg press", "[C]"), ("calf raises", "[C]"), ("crunch inverso addome", "[C]")]

}

EX_BODYWEIGHT = {
    "PUSH": [("push up standard", "[F]"), ("pike push up (spalle)", "[F]"), ("push up inclinati", "[C]"), ("diamond push up", "[C]"), ("dip su sedia", "[C]")],
    "PULL": [("inverted row sotto tavolo", "[F]"), ("pull up alla porta o sbarra", "[F]"), ("isometric hold schiena", "[T]"), ("towel curl bicipiti", "[C]")],
    "LEGS": [("squat a corpo libero", "[F]"), ("affondi alternati", "[C]"), ("affondi bulgari (piede su sedia)", "[C]"), ("wall sit (isometria)", "[T]"), ("glute bridge a una gamba", "[C]")],
    "UPPER": [("push up", "[F]"), ("inverted row", "[F]"), ("pike push up", "[F]"), ("hindu push up", "[C]"), ("plank up", "[T]")],
    "LOWER": [("squat a corpo libero", "[F]"), ("affondi posteriori", "[C]"), ("jump squat esplosivi", "[T]"), ("wall sit", "[T]"), ("calf raises a una gamba", "[C]")],
    "FULL": [("burpees", "[T]"), ("squat a corpo libero", "[F]"), ("push up", "[F]"), ("inverted row", "[F]"), ("plank", "[T]")],
    "HIIT": [("burpees", "[T]"), ("jumping jack", "[T]"), ("mountain climber", "[T]"), ("squat jump", "[T]"), ("high knees / ginocchia alte", "[T]")],
    "CARDIO": [("corsa sul posto", "[T]"), ("jumping jack", "[T]"), ("shadow boxing / kick", "[T]")],
    "CORE": [("plank tradizionale", "[T]"), ("crunch a terra", "[C]"), ("leg raise sdraiato", "[C]"), ("side plank destro/sinistro", "[T]")],
    "RECOMP_FULL": [("squat jump", "[T]"), ("push up", "[F]"), ("inverted row", "[F]"), ("affondi alternati", "[C]"), ("burpees svuotafiato", "[T]")],
    "RECOMP_UPPER": [("push up standard", "[F]"), ("pike push up", "[F]"), ("row sotto il tavolo", "[F]"), ("plank walk", "[C]"), ("jumping jack", "[T]")],
    "RECOMP_LOWER": [("squat corpo libero", "[F]"), ("affondi bulgari", "[C]"), ("glute bridge", "[C]"), ("wall sit", "[T]"), ("mountain climber", "[T]")]
}

EX_HOME = {
    "PUSH": [("floor press con manubri", "[F]"), ("shoulder press manubri", "[F]"), ("push up", "[F]"), ("panca inclinata manubri", "[C]"), ("alzate laterali manubri", "[C]")],
    "PULL": [("trazioni alla sbarra", "[F]"), ("rematore con manubri", "[F]"), ("rematore a un braccio", "[F]"), ("curl bicipiti alternato", "[C]"), ("hammer curl", "[C]")],
    "LEGS": [("goblet squat con manubrio", "[F]"), ("stacco rumeno manubri", "[F]"), ("affondi con manubri", "[C]"), ("affondi bulgari", "[C]"), ("calf raises con peso", "[C]")],
    "UPPER": [("floor press manubri", "[F]"), ("rematore manubri", "[F]"), ("shoulder press manubri", "[F]"), ("curl bicipiti", "[C]"), ("kickback tricipiti", "[C]")],
    "LOWER": [("goblet squat", "[F]"), ("stacco rumeno manubri", "[F]"), ("affondi incrociati", "[C]"), ("leg curl con manubrio tra i piedi", "[C]"), ("calf raises", "[C]")],
    "FULL": [("goblet squat", "[F]"), ("floor press manubri", "[F]"), ("rematore manubri", "[F]"), ("clean & press manubri", "[F]"), ("plank", "[T]")],
    "HIIT": [("burpees", "[T]"), ("jump squat con peso leggero", "[T]"), ("mountain climber", "[T]"), ("kettlebell/dumbbell swing", "[T]")],
    "CARDIO": [("camminata veloce / corsa", "[T]"), ("salti con la corda", "[T]"), ("shadow boxing con pesetti", "[T]")],
    "CORE": [("plank frontale", "[T]"), ("crunch a terra", "[C]"), ("leg raise con piccolo peso", "[C]"), ("russian twist con manubrio", "[C]")],
    "RECOMP_FULL": [("goblet squat", "[F]"), ("floor press manubri", "[F]"), ("rematore manubri", "[F]"), ("affondi manubri", "[C]"), ("squat jump", "[T]")],
    "RECOMP_UPPER": [("panca inclinata manubri", "[F]"), ("rematore a un braccio", "[F]"), ("shoulder press manubri", "[F]"), ("curl + french press manubri", "[C]"), ("jumping jack", "[T]")],
    "RECOMP_LOWER": [("goblet squat", "[F]"), ("stacco rumeno manubri", "[F]"), ("affondi camminati manubri", "[C]"), ("calf raises manubri", "[C]"), ("plank", "[T]")]
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

# =====================================================================
# SPLIT ENGINE (9 COMBINAZIONI STRUTTURATE)
# =====================================================================
def get_split(goal, days):
    days = int(days)
    
    # MASSA
    if goal == "massa":
        if days <= 2:
            return ["FULL", "FULL"] if days == 2 else ["FULL"]
        elif 3 <= days <= 4:
            return ["PUSH", "PULL", "LEGS", "FULL"] if days == 4 else ["PUSH", "PULL", "LEGS"]
        else:
            full_plan = ["PUSH", "PULL", "LEGS", "UPPER", "LOWER", "FULL", "CORE"]
            return full_plan[:days]

    # RICOMPOSIZIONE CORPOREA
    elif goal == "ricomposizione corporea":
        if days <= 2:
            return ["RECOMP_FULL", "RECOMP_FULL"] if days == 2 else ["RECOMP_FULL"]
        elif 3 <= days <= 4:
            return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL", "CORE"] if days == 4 else ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL"]
        else:
            full_plan = ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL", "CORE", "HIIT"]
            return full_plan[:days]

    # DIMAGRIMENTO / CARDIO
    else:
        if days <= 2:
            return ["HIIT", "CARDIO"] if days == 2 else ["HIIT"]
        elif 3 <= days <= 4:
            return ["HIIT", "CORE", "CARDIO", "FULL"] if days == 4 else ["HIIT", "CORE", "CARDIO"]
        else:
            full_plan = ["HIIT", "CARDIO", "CORE", "FULL", "HIIT", "CARDIO", "CORE"]
            return full_plan[:days]

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
# GENERATOR
# =====================================================================
def generate(data):
    days = data.get("days", 3)
    focus = data.get("focus", "full body")
    goal = data.get("goal", "massa")
    level = data.get("level", "livello base")
    
    # Se l'utente seleziona un focus specifico (Upper/Lower), mantiene le precedenze custom, altrimenti usa lo Split Engine
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
        name=str(data.get('name', 'Utente')).title(),
        email=data.get('email', '-'),
        age=data.get('age', '-'),
        height=data.get('height', '-'),
        weight=data.get('weight', '-'),
        level=str(data.get('level', '-')).upper(),
        equipment=str(data.get('equipment', '-')).title(),
        goal=str(data.get('goal', '-')).title(),
        focus=str(data.get('focus', '-')).title(),
        days=days
    )

    days_list = data.get("days_list", [])
    for i in range(days):
        day = days_list[i] if i < len(days_list) else f"Giorno {i+1}"
        type_day = plan[i] if i < len(plan) else "FULL"

        text += f"\n📅 <b>{day.upper()} — {type_day}</b>\n"
        for ex in build(type_day, data.get("equipment", "palestra"), level):
            text += f"- {ex}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    text += "\n⚠️ <i>Questa scheda NON sostituisce il parere di un medico! Seguila soltanto se sei perfettamente in salute.</i>\n"
    return text

# =========================
# WEBHOOK
# =========================
WEBHOOK_SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET", "Zanzibar-secret-ostreghetta")

@app.route("/webhook", methods=["POST"])
def webhook():
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if token != WEBHOOK_SECRET_TOKEN:
        return "Non autorizzato", 403

    data = request.json
    if not data or "message" not in data:
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

    if u["step"] > 1 and not u["data"]:
        u["step"] = 1
        send(chat_id, "⚠️ Sessione scaduta. Ricominciamo!\n👤 Nome e cognome:")
        return "ok"

    # ==========================================
    # MACCHINA A STATI
    # ==========================================
    if u["step"] == 1:
        u["data"]["name"] = raw_text
        u["step"] = 2
        send(chat_id, "📧 Email:")
        return "ok"

    if u["step"] == 2:
        if not is_valid_email(raw_text.strip()):
            send(chat_id, "❌ Email non valida. Reinserisci una mail reale (es: nome@gmail.com):")
            return "ok"
        u["data"]["email"] = raw_text.strip()
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
        
        tastiera_livello = {
            "keyboard": [
                ["mai allenato", "livello base"],
                ["livello avanzato", "esperto"]
            ],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send(chat_id, "📊 Seleziona il tuo livello d'esperienza:", reply_markup=tastiera_livello)
        return "ok"

    if u["step"] == 5:
        if text not in ["mai allenato", "livello base", "livello avanzato", "esperto"]:
            send(chat_id, "❌ Livello non valido. Scegli tra quelli in elenco:")
            return "ok"
        u["data"]["level"] = text
        u["step"] = 6
        
        tastiera_attrezzi = {
            "keyboard": [
                ["corpo libero", "casa", "palestra"]
            ],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send(chat_id, "🏋️ Scegli l'attrezzatura:", reply_markup=tastiera_attrezzi)
        return "ok"

    if u["step"] == 6:
        if text not in ["corpo libero", "casa", "palestra"]:
            send(chat_id, "❌ Attrezzatura non valida. Scegli tra corpo libero, casa o palestra:")
            return "ok"
        u["data"]["equipment"] = text
        u["step"] = 7
        
        tastiera_obiettivo = {
            "keyboard": [
                ["massa", "dimagrimento"],
                ["ricomposizione corporea"]
            ],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send(chat_id, "🎯 Qual è il tuo obiettivo?", reply_markup=tastiera_obiettivo)
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
        
        tastiera_focus = {
            "keyboard": [
                ["upper body", "lower body", "full body"]
            ],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send(chat_id, "💪 Scegli il focus muscolare:", reply_markup=tastiera_focus)
        return "ok"

    if u["step"] == 8:
        if text not in ["upper body", "lower body", "full body"]:
            send(chat_id, "❌ Focus non valido. Scegli tra upper body, lower body o full body:")
            return "ok"
        u["data"]["focus"] = text
        u["step"] = 9
        
        send(chat_id, "📅 Quanti giorni a settimana vuoi allenarti? (1-7):", reply_markup={"remove_keyboard": True})
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

        if len(set(days_list)) != len(days_list):
            send(chat_id, "❌ Hai inserito dei giorni duplicati (es. due volte 'lunedi'). Riprova a elencarli:")
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