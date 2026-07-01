from flask import Flask, request
import requests
import os
import re
from datetime import datetime, timedelta
from supabase import create_client, Client

app = Flask(__name__)

# =====================================================================
# CONFIGURAZIONE CREDENZIALI DIRETTE (HARDCODED)
# =====================================================================
# ⚠️ SOSTITUISCI I VALORI DENTRO LE VIRGOLETTE CON I TUOI DATI REALI
BOT_TOKEN = "IL_TUO_TOKEN_TELEGRAM_REALE" 
URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
IL_TUO_CHAT_ID = 5734151732
WEBHOOK_SECRET_TOKEN = "Zanzibar-secret-ostreghetta"

# Credenziali MuscleWiki e Supabase Database inserite direttamente
MUSCLEWIKI_API_KEY = "LA_TUA_CHIAVE_DI_MUSCLEWIKI"
SUPABASE_URL = "https://kzfapegnsumqkdoytjzk.supabase.co"
SUPABASE_KEY = "LA_TUA_CHIAVE_ANON_PUBLIC_LUNGHISSIMA_DI_SUPABASE"

# Inizializzazione del client Supabase per la Cache
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        response = requests.post(f"{URL}/sendMessage", json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio del messaggio a {chat_id}: {e}")

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
def valid_weight(w): return 40 <= w <= 300
def valid_height(h): return 50 <= h <= 300  

def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

VALID_DAYS = [
    "lunedi", "martedi", "mercoledi",
    "giovedi", "venerdi", "sabato", "domenica"
]

# =====================================================================
# VOLUME ENGINE
# =====================================================================
def get_volume_string(ex_name, ex_type, level):
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
# SPLIT ENGINE
# =====================================================================
def get_split(goal, days):
    days = int(days)
    if goal == "massa":
        if days <= 2: return ["FULL", "FULL"] if days == 2 else ["FULL"]
        elif 3 <= days <= 4: return ["PUSH", "PULL", "LEGS", "FULL"] if days == 4 else ["PUSH", "PULL", "LEGS"]
        else: return ["PUSH", "PULL", "LEGS", "UPPER", "LOWER", "FULL", "CORE"][:days]
    elif goal == "ricomposizione corporea":
        if days <= 2: return ["RECOMP_FULL", "RECOMP_FULL"] if days == 2 else ["RECOMP_FULL"]
        elif 3 <= days <= 4: return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL", "CORE"] if days == 4 else ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL"]
        else: return ["RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_UPPER", "RECOMP_LOWER", "RECOMP_FULL", "CORE", "HIIT"][:days]
    else:
        if days <= 2: return ["HIIT", "CARDIO"] if days == 2 else ["HIIT"]
        elif 3 <= days <= 4: return ["HIIT", "CORE", "CARDIO", "FULL"] if days == 4 else ["HIIT", "CORE", "CARDIO"]
        else: return ["HIIT", "CARDIO", "CORE", "FULL", "HIIT", "CARDIO", "CORE"][:days]

# =====================================================================
# ENGINE CACHE & INTEGRAZIONE MUSCLEWIKI
# =====================================================================
def build(day_type, equipment, level):
    cache_key = f"{day_type}_{equipment}"
    now = datetime.utcnow()
    limite_30_giorni = (now - timedelta(days=30)).isoformat()

    # 1. TENTATIVO DI LETTURA DALLA CACHE DI SUPABASE (Costo API = 0)
    try:
        query = supabase.table("muscle_cache").select("exercises, created_at").eq("cache_key", cache_key).gt("created_at", limite_30_giorni).execute()
        if query.data:
            cached_exercises = query.data[0]["exercises"]
            return [get_volume_string(ex["name"], ex["type"], level) for ex in cached_exercises]
    except Exception as e:
        print(f"Errore lettura cache Supabase: {e}")

    # 2. SE NON C'È NELLA CACHE, CHIEDIAMO A MUSCLEWIKI API
    eq_map = {
        "corpo libero": "bodyweight",
        "casa": "dumbbell",
        "palestra": "barbell"
    }
    mw_equipment = eq_map.get(equipment, "bodyweight")

    muscle_groups = []
    if "PUSH" in day_type or "UPPER" in day_type:
        muscle_groups = ["chest", "shoulders", "triceps"]
    elif "PULL" in day_type:
        muscle_groups = ["lats", "lower_back", "biceps"]
    elif "LEGS" in day_type or "LOWER" in day_type:
        muscle_groups = ["quads", "hamstrings", "glutes", "calves"]
    elif "CORE" in day_type:
        muscle_groups = ["abs"]
    else:
        muscle_groups = ["chest", "lats", "quads", "abs"]

    api_url = "https://api.musclewiki.com/v1/exercises"
    headers = {
        "Authorization": f"Bearer {MUSCLEWIKI_API_KEY}",
        "Accept-Language": "it"
    }

    raw_exercises_to_cache = []
    output_exercises = []
    
    for muscle in muscle_groups[:2]: 
        params = {
            "muscle": muscle,
            "equipment": mw_equipment,
            "limit": 3
        }
        try:
            res = requests.get(api_url, headers=headers, params=params, timeout=8)
            if res.status_code == 200:
                for item in res.json().get("exercises", []):
                    ex_name = item.get("name", "Esercizio")
                    ex_type = "[F]" if any(x in ex_name.lower() for x in ["panca", "squat", "stacco"]) else "[C]"
                    
                    if not any(e["name"] == ex_name for e in raw_exercises_to_cache):
                        raw_exercises_to_cache.append({"name": ex_name, "type": ex_type})
                        
                    vol_str = get_volume_string(ex_name, ex_type, level)
                    if vol_str not in output_exercises:
                        output_exercises.append(vol_str)
        except Exception as e:
            print(f"Errore chiamata MuscleWiki: {e}")
            break

    # 3. SALVIAMO I DATI SU SUPABASE PER I PROSSIMI 30 GIORNI
    if raw_exercises_to_cache:
        try:
            supabase.table("muscle_cache").delete().eq("cache_key", cache_key).execute()
            supabase.table("muscle_cache").insert({
                "cache_key": cache_key,
                "exercises": raw_exercises_to_cache,
                "created_at": now.isoformat()
            }).execute()
        except Exception as e:
            print(f"Errore scrittura cache Supabase: {e}")

    # Fallback d'emergenza se l'API e la cache falliscono insieme
    if not output_exercises:
        return [
            f"Squat a {equipment} 3x10", 
            f"Spinte/Piegamenti 3x10", 
            f"Trazioni/Rematore 3x12", 
            f"Plank addome 3x45s"
        ]

    return output_exercises[:6]

# =====================================================================
# GENERATOR
# =====================================================================
def generate(data):
    days = data.get("days", 3)
    focus = data.get("focus", "full body")
    goal = data.get("goal", "massa")
    level = data.get("level", "livello base")
    
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

⚠️ <i>Nota: I prezzi e gli sconti all'interno del canale sono aggiornati costantemente ma sono da intendersi come <b>prezzi validi esclusivamente al momento dell'invio del messaggio</b>. Le promozioni di Amazon possono variare o scadere rapidamente in base alla disponibilità.</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━

🏋️ <b>IL TUO PIANO PERSONALIZZATO (Smart Cache Active)</b>

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
    # MACCHINA A STATI (Raccolta Dati Lead)
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
        raw = norm(raw_text).replace(",", " ")
        days_list = raw.split()

        for d in days_list:
            if d not in VALID_DAYS:
                send(chat_id, f"❌ Giorno non riconosciuto: '{d}'. Riprova a elencarli tutti (senza accenti, es: lunedi):")
                return "ok"

        if len(set(days_list)) != len(days_list):
            send(chat_id, "❌ Hai inserito dei giorni duplicati. Riprova a elencarli:")
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
    return "Bot attivo e collegato correttamente a MuscleWiki e Supabase DB!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
