#!/usr/bin/env python3
"""
klik_agent v5.0 — Lovable Bot + Leads Bot + Tasks Bot
Bots: @klik_lovable_bot | @klik_leads_bot | @Matan_klik_Architectbot
"""
from flask import Flask, request, jsonify
import requests, logging, os, time, json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── ENV ──────────────────────────────────────────────────────────
LOVABLE_TOKEN = os.environ.get("BOT_TOKEN",        "").strip()
LEADS_TOKEN   = os.environ.get("LEADS_BOT_TOKEN",  "").strip()
TASKS_TOKEN   = os.environ.get("TASKS_BOT_TOKEN",  "8749435051:AAGQh4udNta3qJzeZta5N5dMfcuUqvJqEDQ").strip()
CHAT_ID       = int(os.environ.get("CHAT_ID",       "326460077"))
LOVABLE_URL   = os.environ.get("LOVABLE_URL",
    "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325").strip()

# ── GUMLOOP ───────────────────────────────────────────────────────
GUMLOOP_API_KEY  = "f68e93c16aad4774aa204e7b19fb6aa9"
GUMLOOP_USER_ID  = "3IeYf3BuDTSBYlmFOlgIGBiDOLs2"
GUMLOOP_PIPELINE = "mi7pWhLDxKFDFqYii16B2v"
GUMLOOP_URL_API  = "https://api.gumloop.com/api/v1/start_pipeline"

# ── CONST ─────────────────────────────────────────────────────────
NA   = "לא צוין"
HIGH = "גבוהה"
MED  = "בינונית"
LOW  = "נמוכה"
PRIORITY_ICON = {HIGH: "🔴", MED: "🟡", LOW: "🟢"}

# ── STORE ─────────────────────────────────────────────────────────
STORE_FILE = "request_store.json"
request_store = {}
user_state = {}

def load_store():
    global request_store
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                request_store = json.load(f)
            logging.info("[store] loaded %d records", len(request_store))
        except Exception as e:
            logging.error("[store] load error: %s", e)
            request_store = {}

def save_store():
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(request_store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("[store] save error: %s", e)

def make_rid(data, prefix="req"):
    raw = (data.get("id") or "").strip()
    return raw if raw else prefix + "_" + str(int(time.time()))

# ── TELEGRAM ──────────────────────────────────────────────────────
def tg(token, method, payload, timeout=10):
    if not token:
        logging.error("[tg] token missing for %s", method)
        return {"ok": False}
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + token + "/" + method,
            json=payload, timeout=timeout
        )
        res = r.json()
        logging.info("[tg] %s ok=%s", method, res.get("ok"))
        return res
    except Exception as e:
        logging.error("[tg] %s error: %s", method, e)
        return {"ok": False}

def tg_send(token, chat_id, text, keyboard=None):
    p = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        p["reply_markup"] = {"inline_keyboard": keyboard}
    return tg(token, "sendMessage", p)

def tg_edit(token, chat_id, message_id, text, keyboard=None):
    p = {"chat_id": chat_id, "message_id": message_id,
         "text": text, "parse_mode": "HTML"}
    if keyboard:
        p["reply_markup"] = {"inline_keyboard": keyboard}
    return tg(token, "editMessageText", p)

def tg_answer(token, cb_id, text="OK", alert=False):
    return tg(token, "answerCallbackQuery",
              {"callback_query_id": cb_id, "text": text, "show_alert": alert}, timeout=5)

# ── PHONE HELPER ──────────────────────────────────────────────────
def clean_phone(phone):
    d = (phone or "").replace("-", "").replace(" ", "").replace("+", "")
    if d.startswith("972"):
        return d
    return "972" + d.lstrip("0")

# ── GUMLOOP HELPER ────────────────────────────────────────────────
def trigger_gumloop(action, message="", user_id=""):
    payload = {
        "user_id":       GUMLOOP_USER_ID,
        "saved_item_id": GUMLOOP_PIPELINE,
        "pipeline_inputs": [
            {"input_name": "action",  "value": action},
            {"input_name": "message", "value": message},
            {"input_name": "user_id", "value": str(user_id)},
        ],
    }
    try:
        r = requests.post(
            GUMLOOP_URL_API,
            params={"api_key": GUMLOOP_API_KEY},
            json=payload,
            timeout=10,
        )
        res = r.json()
        logging.info("[gumloop] action=%s run_id=%s", action, res.get("run_id"))
        return res
    except Exception as e:
        logging.error("[gumloop] error: %s", e)
        return {}

# ── TASKS KEYBOARD ────────────────────────────────────────────────
def tasks_keyboard():
    return [
        [
            {"text": "✅ הוסף למשימות", "callback_data": "task_add"},
            {"text": "❌ לא תודה",       "callback_data": "task_dismiss"},
        ],
        [
            {"text": "🚀 שפר ביצוע",        "callback_data": "task_improve"},
            {"text": "⏰ תזכיר לי מאוחר", "callback_data": "task_remind"},
        ],
    ]

# ══════════════════════════════════════════════════════════════════
#  TASKS BOT — @Matan_klik_Architectbot
# ══════════════════════════════════════════════════════════════════

@app.route("/webhook/tasks", methods=["POST"])
def tasks_webhook():
    try:
        upd = request.get_json(silent=True) or {}
        logging.info("[tasks] update: %s", str(upd)[:300])

        if "callback_query" in upd:
            cb      = upd["callback_query"]
            cb_id   = cb.get("id", "")
            cb_data = (cb.get("data") or "").strip()
            msg     = cb.get("message", {})
            msg_id  = msg.get("message_id")
            chat_id = msg.get("chat", {}).get("id")
            user_id = cb.get("from", {}).get("id", "")
            name    = cb.get("from", {}).get("first_name", "משתמש")

            tg_answer(TASKS_TOKEN, cb_id)

            if cb_data == "task_add":
                user_state[user_id] = "awaiting_task"
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "✍️ מה המשימה? כתוב לי אותה:")

            elif cb_data == "task_dismiss":
                trigger_gumloop("dismiss", user_id=user_id)
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "בסדר! 😊 כשתצטרך — אני כאן.",
                        tasks_keyboard())

            elif cb_data == "task_improve":
                trigger_gumloop("improve", user_id=user_id)
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "🔥 " + name + ", הגיע הזמן להתקדם!\n\nבחר משימה אחת קטנה — ועשה אותה עכשיו. 💪",
                        tasks_keyboard())

            elif cb_data == "task_remind":
                user_state[user_id] = "awaiting_remind_time"
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "⏰ בעוד כמה זמן תרצה תזכורת?\nלדוגמא: <b>30 דקות</b>, <b>שעה</b>, <b>מחר בבוקר</b>")

            return jsonify({"ok": True}), 200

        if "message" in upd:
            msg     = upd["message"]
            text    = (msg.get("text") or "").strip()
            chat_id = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id", "")
            name    = msg.get("from", {}).get("first_name", "משתמש")
            state   = user_state.get(user_id)

            if text.startswith("/start"):
                tg_send(TASKS_TOKEN, chat_id,
                        "היי " + name + "! 👋 מה נעשה?",
                        tasks_keyboard())

            elif state == "awaiting_task":
                del user_state[user_id]
                trigger_gumloop("add_task", message=text, user_id=user_id)
                tg_send(TASKS_TOKEN, chat_id,
                        "✅ המשימה נוספה!\n📝 <b>" + text + "</b>",
                        tasks_keyboard())

            elif state == "awaiting_remind_time":
                del user_state[user_id]
                trigger_gumloop("remind_later", message=text, user_id=user_id)
                tg_send(TASKS_TOKEN, chat_id,
                        "⏰ אזכיר לך בעוד " + text + " ✔️",
                        tasks_keyboard())

            else:
                tg_send(TASKS_TOKEN, chat_id,
                        "מה תרצה לעשות? 👇",
                        tasks_keyboard())

        return jsonify({"ok": True}), 200

    except Exception as e:
        logging.exception("[tasks] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ══════════════════════════════════════════════════════════════════
#  LOVABLE BOT
# ══════════════════════════════════════════════════════════════════

def lovable_keyboard(rid):
    return [
        [{"text": "✅ אשר", "callback_data": "approve:" + rid},
         {"text": "❌ דחה", "callback_data": "reject:"  + rid}],
        [{"text": "✨ שפר פרומפט", "callback_data": "improve_prompt:" + rid},
         {"text": "📊 סטטוס",      "callback_data": "status:" + rid}],
        [{"text": "🚀 שלח ל-Lovable", "callback_data": "send_to_lovable:" + rid},
         {"text": "🔗 פתח Lovable",   "url": LOVABLE_URL}],
    ]

def lovable_small_kb(rid):
    return [
        [{"text": "🚀 שלח ל-Lovable", "callback_data": "send_to_lovable:" + rid},
         {"text": "📊 סטטוס",         "callback_data": "status:" + rid}],
        [{"text": "🔗 Lovable", "url": LOVABLE_URL}],
    ]

def build_lovable_prompt(data):
    feature  = data.get("feature")      or NA
    priority = data.get("priority")     or NA
    req_by   = data.get("requested_by") or NA
    details  = data.get("details")      or NA
    pe       = PRIORITY_ICON.get(priority, "🟣")
    return "\n".join([
        "✨ <b>פרומפט פרמיום ל-Lovable</b>", "",
        "<b>1️⃣ מטרה</b>",
        "להטמיע את הפיצ׳ר: <b>" + feature + "</b>", "",
        "<b>2️⃣ הבעיה</b>", details, "",
        "<b>3️⃣ מה צריך לשנות</b>",
        "• עדכן את ה-UI אם נדרש",
        "• עדכן לוגיקה עסקית בלבד",
        "• אפס שינויים שלא קשורים", "",
        "<b>4️⃣ דרישות</b>",
        "• פיצ׳ר: " + feature,
        "• עדיפות: " + pe + " " + priority,
        "• מבקש: " + req_by,
        "• פירוט: " + details, "",
        "<b>5️⃣ מגבלות</b>",
        "• לא לשנות קוד שלא קשור",
        "• לא לשבור פיצ׳רים קיימים", "",
        "<b>6️⃣ תוצאה רצויה</b>",
        "הפיצ׳ר \"" + feature + "\" עובד במלואו ובצורה יציבה.",
    ])

@app.route("/webhook/lovable", methods=["POST"])
def lovable_webhook():
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "empty"}), 400
        rid = make_rid(data, "req")
        now = time.time()
        request_store[rid] = {"type": "lovable", "data": data,
                               "improved_prompt": None, "status": "created",
                               "created_at": now, "updated_at": now}
        save_store()
        feature  = data.get("feature")      or NA
        priority = data.get("priority")     or NA
        req_by   = data.get("requested_by") or NA
        details  = data.get("details")      or NA
        pe       = PRIORITY_ICON.get(priority, "🟣")
        text = ("🟣 <b>בקשה חדשה ב-Lovable!</b>\n"
                "🪄 " + feature + "\n" + pe + " " + priority + "\n"
                "👤 " + req_by + "\n📝 " + details + "\n🔑 ID: " + rid)
        res = tg_send(LOVABLE_TOKEN, CHAT_ID, text, lovable_keyboard(rid))
        return jsonify({"status": "ok", "request_id": rid, "telegram_ok": res.get("ok")}), 200
    except Exception as e:
        logging.exception("[lovable] exception")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook/callback", methods=["POST"])
def lovable_callback():
    try:
        upd     = request.get_json(silent=True) or {}
        cb      = upd.get("callback_query", {})
        cb_id   = cb.get("id", "")
        cb_data = (cb.get("data") or "").strip()
        msg     = cb.get("message", {})
        msg_id  = msg.get("message_id")
        chat_id = msg.get("chat", {}).get("id", CHAT_ID)
        if not cb_data or ":" not in cb_data:
            tg_answer(LOVABLE_TOKEN, cb_id, "אין נתון", True)
            return jsonify({"ok": True}), 200
        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()
        if action == "improve_prompt":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID לא נמצא", True)
                return jsonify({"ok": True}), 200
            prompt = build_lovable_prompt(store["data"])
            store.update({"improved_prompt": prompt, "status": "improved", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "פרומפט שופר!")
            tg_edit(LOVABLE_TOKEN, chat_id, msg_id, prompt, lovable_small_kb(rid))
        elif action == "send_to_lovable":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID לא נמצא", True)
                return jsonify({"ok": True}), 200
            prompt  = store.get("improved_prompt") or build_lovable_prompt(store["data"])
            feature = store["data"].get("feature") or NA
            store.update({"status": "sent", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "נשלח!")
            tg_send(LOVABLE_TOKEN, chat_id,
                    "🚀 <b>שליחה ל-Lovable</b>\n🔑 " + rid + "\n🪄 " + feature + "\n\n" + prompt,
                    [[{"text": "🔗 פתח Lovable", "url": LOVABLE_URL}],
                     [{"text": "📊 סטטוס", "callback_data": "status:" + rid}]])
        elif action == "status":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID לא נמצא", True)
                return jsonify({"ok": True}), 200
            feature = store["data"].get("feature") or NA
            tg_answer(LOVABLE_TOKEN, cb_id, "סטטוס טעון")
            tg_send(LOVABLE_TOKEN, chat_id,
                    "📊 <b>סטטוס</b>\n🔑 " + rid + "\n🪄 " + feature +
                    "\n📌 מצב: " + store.get("status","unknown") +
                    "\n✨ פרומפט: " + ("✅ כן" if store.get("improved_prompt") else "❌ טרם"),
                    lovable_small_kb(rid))
        elif action == "approve":
            if store: store.update({"status": "approved", "updated_at": now}); save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "אושר!")
            tg_send(LOVABLE_TOKEN, chat_id, "✅ בקשה " + rid + " אושרה!")
        elif action == "reject":
            if store: store.update({"status": "rejected", "updated_at": now}); save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "נדחה")
            tg_send(LOVABLE_TOKEN, chat_id, "❌ בקשה " + rid + " נדחתה.")
        else:
            tg_answer(LOVABLE_TOKEN, cb_id)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logging.exception("[lovable_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ══════════════════════════════════════════════════════════════════
#  LEADS BOT
# ══════════════════════════════════════════════════════════════════

def leads_keyboard(rid, phone=""):
    phone_clean = clean_phone(phone) if phone else ""
    kb = []
    if phone_clean:
        kb.append([
            {"text": "📞 התקשר עכשיו",
             "url": "https://wa.me/" + phone_clean + "?text=שלום, אני מצוות קליק"},
            {"text": "💬 WhatsApp", "url": "https://wa.me/" + phone_clean},
        ])
    kb.append([
        {"text": "✅ פתוח", "callback_data": "lead_open:"    + rid},
        {"text": "❌ סגור", "callback_data": "lead_close:"   + rid},
    ])
    kb.append([
        {"text": "⏰ תזכורת 2ש", "callback_data": "lead_snooze:"  + rid},
        {"text": "✨ שפר פרומפט", "callback_data": "lead_improve:" + rid},
    ])
    return kb

def build_lead_prompt(data):
    name        = data.get("name")        or NA
    service     = data.get("service")     or NA
    location    = data.get("location")    or NA
    description = data.get("description") or NA
    return "\n".join([
        "✨ <b>פרומפט פרמיום ל-Lovable</b>", "",
        "<b>1️⃣ מטרה</b>",
        "לשפר את דף <b>" + service + "</b> מאזור " + location + ".", "",
        "<b>2️⃣ הקשר</b>",
        "ליד: " + name + " מ" + location + " ביקש " + service + ".",
        "צורך: " + description, "",
        "<b>3️⃣ מה לשפר</b>",
        "• דף שירות " + service + " עם תמונות",
        "• CTA לוואטסאפ/טלפון",
        "• טופס ביצוע מהיר", "",
        "<b>4️⃣ תוצאה רצויה</b>",
        "דף " + service + " ב" + location + " ממיר לידים.",
    ])

@app.route("/webhook/leads", methods=["POST"])
def leads_webhook():
    try:
        data  = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "empty"}), 400
        rid   = make_rid(data, "lead")
        now   = time.time()
        phone = data.get("phone", "")
        request_store[rid] = {"type": "lead", "data": data,
                               "lead_prompt": None, "status": "new",
                               "created_at": now, "updated_at": now}
        save_store()
        name     = data.get("name")        or NA
        service  = data.get("service")     or NA
        location = data.get("location")    or NA
        desc     = data.get("description") or NA
        text = ("🔥 <b>ליד חדש!</b>\n👤 " + name + "\n🔧 " + service +
                "\n📍 " + location + "\n" +
                ("📞 " + phone + "\n" if phone else "") +
                "📝 " + desc + "\n🔑 ID: " + rid)
        res = tg_send(LEADS_TOKEN, CHAT_ID, text, leads_keyboard(rid, phone))
        return jsonify({"status": "ok", "request_id": rid, "telegram_ok": res.get("ok")}), 200
    except Exception as e:
        logging.exception("[leads] exception")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook/callback/leads", methods=["POST"])
def leads_callback():
    try:
        upd     = request.get_json(silent=True) or {}
        cb      = upd.get("callback_query", {})
        cb_id   = cb.get("id", "")
        cb_data = (cb.get("data") or "").strip()
        msg     = cb.get("message", {})
        chat_id = msg.get("chat", {}).get("id", CHAT_ID)
        if not cb_data or ":" not in cb_data:
            tg_answer(LEADS_TOKEN, cb_id, "אין נתון", True)
            return jsonify({"ok": True}), 200
        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()
        if action == "lead_open":
            if store: store.update({"status": "open", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "ליד פתוח")
            tg_send(LEADS_TOKEN, chat_id, "✅ ליד " + rid + " סומן כפתוח!")
        elif action == "lead_close":
            if store: store.update({"status": "closed", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "ליד נסגר")
            tg_send(LEADS_TOKEN, chat_id, "❌ ליד " + rid + " נסגר.")
        elif action == "lead_snooze":
            if store: store.update({"status": "snoozed", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "תזכורת 2ש נקבעה")
            tg_send(LEADS_TOKEN, chat_id, "⏰ תזכורת לליד " + rid + " ל-2 שעות.")
        elif action == "lead_improve":
            if not store:
                tg_answer(LEADS_TOKEN, cb_id, "RID לא נמצא", True)
                return jsonify({"ok": True}), 200
            prompt = build_lead_prompt(store["data"])
            store.update({"lead_prompt": prompt, "status": "prompt_ready", "updated_at": now})
            save_store()
            tg_answer(LEADS_TOKEN, cb_id, "פרומפט מוכן!")
            tg_send(LEADS_TOKEN, chat_id, prompt,
                    [[{"text": "🔗 פתח Lovable", "url": LOVABLE_URL}]])
        else:
            tg_answer(LEADS_TOKEN, cb_id)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logging.exception("[leads_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ── HEALTH ────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "klik_agent v5.0 running"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "version": "5.0",
        "lovable_token": bool(LOVABLE_TOKEN),
        "leads_token":   bool(LEADS_TOKEN),
        "tasks_token":   bool(TASKS_TOKEN),
        "requests":      len(request_store),
    }), 200

# ── START ─────────────────────────────────────────────────────────
load_store()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("klik_agent v5.0 — port " + str(port))
    app.run(host="0.0.0.0", port=port, debug=False)
