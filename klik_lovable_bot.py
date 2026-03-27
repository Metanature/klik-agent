#!/usr/bin/env python3
# klik_agent v5.0 - Lovable Bot + Leads Bot + Tasks Bot
# Bots: @klik_lovable_bot | @klik_leads_bot | @Matan_klik_Architectbot

from flask import Flask, request, jsonify
import requests, logging, os, time, json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ENV
LOVABLE_TOKEN = os.environ.get("BOT_TOKEN",        "").strip()
LEADS_TOKEN   = os.environ.get("LEADS_BOT_TOKEN",  "").strip()
TASKS_TOKEN   = os.environ.get("TASKS_BOT_TOKEN",  "").strip()
CHAT_ID       = int(os.environ.get("CHAT_ID", "326460077"))
LOVABLE_URL   = os.environ.get("LOVABLE_URL",
    "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325").strip()

# GUMLOOP
GUMLOOP_API_KEY  = "f68e93c16aad4774aa204e7b19fb6aa9"
GUMLOOP_USER_ID  = "3IeYf3BuDTSBYlmFOlgIGBiDOLs2"
GUMLOOP_PIPELINE = "mi7pWhLDxKFDFqYii16B2v"
GUMLOOP_URL_API  = "https://api.gumloop.com/api/v1/start_pipeline"

# CONST
NA   = "×œ× ×¦×•×™×Ÿ"
HIGH = "×’×‘×•×”×”"
MED  = "×‘×™× ×•× ×™×ª"
LOW  = "× ×ž×•×›×”"
PRIORITY_ICON = {HIGH: "ðŸ”´", MED: "ðŸŸ¡", LOW: "ðŸŸ¢"}

# STORE
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

# TELEGRAM
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

def clean_phone(phone):
    d = (phone or "").replace("-", "").replace(" ", "").replace("+", "")
    if d.startswith("972"):
        return d
    return "972" + d.lstrip("0")

# GUMLOOP
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

# TASKS KEYBOARD
def tasks_keyboard():
    return [
        [
            {"text": "âœ… ×”×•×¡×£ ×œ×ž×©×™×ž×•×ª", "callback_data": "task_add"},
            {"text": "âŒ ×œ× ×ª×•×“×”",       "callback_data": "task_dismiss"},
        ],
        [
            {"text": "ðŸš€ ×©×¤×¨ ×‘×™×¦×•×¢",        "callback_data": "task_improve"},
            {"text": "â° ×ª×–×›×™×¨ ×œ×™ ×ž××•×—×¨", "callback_data": "task_remind"},
        ],
    ]

# =========================================================
# TASKS BOT - @Matan_klik_Architectbot
# webhook: /webhook/tasks
# =========================================================

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
            name    = cb.get("from", {}).get("first_name", "×ž×©×ª×ž×©")

            tg_answer(TASKS_TOKEN, cb_id)

            if cb_data == "task_add":
                user_state[user_id] = "awaiting_task"
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "âœï¸ ×ž×” ×”×ž×©×™×ž×”? ×›×ª×•×‘ ×œ×™ ××•×ª×”:")

            elif cb_data == "task_dismiss":
                trigger_gumloop("dismiss", user_id=user_id)
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "×‘×¡×“×¨! ðŸ˜Š ×›×©×ª×¦×˜×¨×š - ×× ×™ ×›××Ÿ.",
                        tasks_keyboard())

            elif cb_data == "task_improve":
                trigger_gumloop("improve", user_id=user_id)
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "ðŸ”¥ " + name + ", ×”×’×™×¢ ×”×–×ž×Ÿ ×œ×”×ª×§×“×!\n\n×‘×—×¨ ×ž×©×™×ž×” ××—×ª ×§×˜× ×” ×•×¢×©×” ××•×ª×” ×¢×›×©×™×•. ðŸ’ª",
                        tasks_keyboard())

            elif cb_data == "task_remind":
                user_state[user_id] = "awaiting_remind_time"
                tg_edit(TASKS_TOKEN, chat_id, msg_id,
                        "â° ×‘×¢×•×“ ×›×ž×” ×–×ž×Ÿ ×ª×¨×¦×” ×ª×–×›×•×¨×ª?\n×œ×“×•×’×ž×: 30 ×“×§×•×ª, ×©×¢×”, ×ž×—×¨ ×‘×‘×•×§×¨")

            return jsonify({"ok": True}), 200

        if "message" in upd:
            msg     = upd["message"]
            text    = (msg.get("text") or "").strip()
            chat_id = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id", "")
            name    = msg.get("from", {}).get("first_name", "×ž×©×ª×ž×©")
            state   = user_state.get(user_id)

            if text.startswith("/start"):
                tg_send(TASKS_TOKEN, chat_id,
                        "×”×™×™ " + name + "! ðŸ‘‹ ×ž×” × ×¢×©×”?",
                        tasks_keyboard())

            elif state == "awaiting_task":
                del user_state[user_id]
                trigger_gumloop("add_task", message=text, user_id=user_id)
                tg_send(TASKS_TOKEN, chat_id,
                        "âœ… ×”×ž×©×™×ž×” × ×•×¡×¤×”!\nðŸ“ <b>" + text + "</b>",
                        tasks_keyboard())

            elif state == "awaiting_remind_time":
                del user_state[user_id]
                trigger_gumloop("remind_later", message=text, user_id=user_id)
                tg_send(TASKS_TOKEN, chat_id,
                        "â° ××–×›×™×¨ ×œ×š ×‘×¢×•×“ " + text + " âœ”ï¸",
                        tasks_keyboard())

            else:
                tg_send(TASKS_TOKEN, chat_id,
                        "×ž×” ×ª×¨×¦×” ×œ×¢×©×•×ª? ðŸ‘‡",
                        tasks_keyboard())

        return jsonify({"ok": True}), 200

    except Exception as e:
        logging.exception("[tasks] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# =========================================================
# LOVABLE BOT
# =========================================================

def lovable_keyboard(rid):
    return [
        [{"text": "âœ… ××©×¨", "callback_data": "approve:" + rid},
         {"text": "âŒ ×“×—×”", "callback_data": "reject:"  + rid}],
        [{"text": "âœ¨ ×©×¤×¨ ×¤×¨×•×ž×¤×˜", "callback_data": "improve_prompt:" + rid},
         {"text": "ðŸ“Š ×¡×˜×˜×•×¡",      "callback_data": "status:" + rid}],
        [{"text": "ðŸš€ ×©×œ×— ×œ-Lovable", "callback_data": "send_to_lovable:" + rid},
         {"text": "ðŸ”— ×¤×ª×— Lovable",   "url": LOVABLE_URL}],
    ]

def lovable_small_kb(rid):
    return [
        [{"text": "ðŸš€ ×©×œ×— ×œ-Lovable", "callback_data": "send_to_lovable:" + rid},
         {"text": "ðŸ“Š ×¡×˜×˜×•×¡",         "callback_data": "status:" + rid}],
        [{"text": "ðŸ”— Lovable", "url": LOVABLE_URL}],
    ]

def build_lovable_prompt(data):
    feature  = data.get("feature")      or NA
    priority = data.get("priority")     or NA
    req_by   = data.get("requested_by") or NA
    details  = data.get("details")      or NA
    pe       = PRIORITY_ICON.get(priority, "ðŸŸ£")
    lines = [
        "âœ¨ <b>×¤×¨×•×ž×¤×˜ ×¤×¨×ž×™×•× ×œ-Lovable</b>", "",
        "<b>1. ×ž×˜×¨×”</b>",
        "×œ×”×˜×ž×™×¢ ××ª ×”×¤×™×¦'×¨: <b>" + feature + "</b>", "",
        "<b>2. ×”×‘×¢×™×”</b>", details, "",
        "<b>3. ×ž×” ×¦×¨×™×š ×œ×©× ×•×ª</b>",
        "- ×¢×“×›×Ÿ ××ª ×”-UI ×× × ×“×¨×©",
        "- ×¢×“×›×Ÿ ×œ×•×’×™×§×” ×¢×¡×§×™×ª ×‘×œ×‘×“",
        "- ××¤×¡ ×©×™× ×•×™×™× ×©×œ× ×§×©×•×¨×™×", "",
        "<b>4. ×“×¨×™×©×•×ª</b>",
        "- ×¤×™×¦'×¨: " + feature,
        "- ×¢×“×™×¤×•×ª: " + pe + " " + priority,
        "- ×ž×‘×§×©: " + req_by,
        "- ×¤×™×¨×•×˜: " + details, "",
        "<b>5. ×ª×•×¦××” ×¨×¦×•×™×”</b>",
        '×”×¤×™×¦\'×¨ "' + feature + '" ×¢×•×‘×“ ×‘×ž×œ×•××• ×•×‘×¦×•×¨×” ×™×¦×™×‘×”.',
    ]
    return "\n".join(lines)

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
        pe       = PRIORITY_ICON.get(priority, "ðŸŸ£")
        text = ("ðŸŸ£ <b>×‘×§×©×” ×—×“×©×” ×‘-Lovable!</b>\n"
                "ðŸª„ " + feature + "\n" + pe + " " + priority + "\n"
                "ðŸ‘¤ " + req_by + "\nðŸ“ " + details + "\nðŸ”‘ ID: " + rid)
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
            tg_answer(LOVABLE_TOKEN, cb_id, "××™×Ÿ × ×ª×•×Ÿ", True)
            return jsonify({"ok": True}), 200
        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()
        if action == "improve_prompt":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID ×œ× × ×ž×¦×", True)
                return jsonify({"ok": True}), 200
            prompt = build_lovable_prompt(store["data"])
            store.update({"improved_prompt": prompt, "status": "improved", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "×¤×¨×•×ž×¤×˜ ×©×•×¤×¨!")
            tg_edit(LOVABLE_TOKEN, chat_id, msg_id, prompt, lovable_small_kb(rid))
        elif action == "send_to_lovable":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID ×œ× × ×ž×¦×", True)
                return jsonify({"ok": True}), 200
            prompt  = store.get("improved_prompt") or build_lovable_prompt(store["data"])
            feature = store["data"].get("feature") or NA
            store.update({"status": "sent", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "× ×©×œ×—!")
            tg_send(LOVABLE_TOKEN, chat_id,
                    "ðŸš€ <b>×©×œ×™×—×” ×œ-Lovable</b>\nðŸ”‘ " + rid + "\nðŸª„ " + feature + "\n\n" + prompt,
                    [[{"text": "ðŸ”— ×¤×ª×— Lovable", "url": LOVABLE_URL}],
                     [{"text": "ðŸ“Š ×¡×˜×˜×•×¡", "callback_data": "status:" + rid}]])
        elif action == "status":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID ×œ× × ×ž×¦×", True)
                return jsonify({"ok": True}), 200
            feature = store["data"].get("feature") or NA
            tg_answer(LOVABLE_TOKEN, cb_id, "×¡×˜×˜×•×¡ ×˜×¢×•×Ÿ")
            tg_send(LOVABLE_TOKEN, chat_id,
                    "ðŸ“Š <b>×¡×˜×˜×•×¡</b>\nðŸ”‘ " + rid + "\nðŸª„ " + feature +
                    "\nðŸ“Œ ×ž×¦×‘: " + store.get("status", "unknown") +
                    "\nâœ¨ ×¤×¨×•×ž×¤×˜: " + ("âœ… ×›×Ÿ" if store.get("improved_prompt") else "âŒ ×˜×¨×"),
                    lovable_small_kb(rid))
        elif action == "approve":
            if store: store.update({"status": "approved", "updated_at": now}); save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "××•×©×¨!")
            tg_send(LOVABLE_TOKEN, chat_id, "âœ… ×‘×§×©×” " + rid + " ××•×©×¨×”!")
        elif action == "reject":
            if store: store.update({"status": "rejected", "updated_at": now}); save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "× ×“×—×”")
            tg_send(LOVABLE_TOKEN, chat_id, "âŒ ×‘×§×©×” " + rid + " × ×“×—×ª×”.")
        else:
            tg_answer(LOVABLE_TOKEN, cb_id)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logging.exception("[lovable_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# =========================================================
# LEADS BOT
# =========================================================

def leads_keyboard(rid, phone=""):
    phone_clean = clean_phone(phone) if phone else ""
    kb = []
    if phone_clean:
        kb.append([
            {"text": "ðŸ“ž ×”×ª×§×©×¨ ×¢×›×©×™×•",
             "url": "https://wa.me/" + phone_clean + "?text=×©×œ×•×, ×× ×™ ×ž×¦×•×•×ª ×§×œ×™×§"},
            {"text": "ðŸ’¬ WhatsApp", "url": "https://wa.me/" + phone_clean},
        ])
    kb.append([
        {"text": "âœ… ×¤×ª×•×—", "callback_data": "lead_open:"    + rid},
        {"text": "âŒ ×¡×’×•×¨", "callback_data": "lead_close:"   + rid},
    ])
    kb.append([
        {"text": "â° ×ª×–×›×•×¨×ª 2×©", "callback_data": "lead_snooze:"  + rid},
        {"text": "âœ¨ ×©×¤×¨ ×¤×¨×•×ž×¤×˜", "callback_data": "lead_improve:" + rid},
    ])
    return kb

def build_lead_prompt(data):
    name        = data.get("name")        or NA
    service     = data.get("service")     or NA
    location    = data.get("location")    or NA
    description = data.get("description") or NA
    lines = [
        "âœ¨ <b>×¤×¨×•×ž×¤×˜ ×¤×¨×ž×™×•× ×œ-Lovable</b>", "",
        "<b>1. ×ž×˜×¨×”</b>",
        "×œ×©×¤×¨ ××ª ×“×£ <b>" + service + "</b> ×ž××–×•×¨ " + location + ".", "",
        "<b>2. ×”×§×©×¨</b>",
        "×œ×™×“: " + name + " ×ž" + location + " ×‘×™×§×© " + service + ".",
        "×¦×•×¨×š: " + description, "",
        "<b>3. ×ž×” ×œ×©×¤×¨</b>",
        "- ×“×£ ×©×™×¨×•×ª " + service + " ×¢× ×ª×ž×•× ×•×ª",
        "- CTA ×œ×•×•××˜×¡××¤/×˜×œ×¤×•×Ÿ",
        "- ×˜×•×¤×¡ ×‘×™×¦×•×¢ ×ž×”×™×¨", "",
        "<b>4. ×ª×•×¦××” ×¨×¦×•×™×”</b>",
        "×“×£ " + service + " ×‘" + location + " ×ž×ž×™×¨ ×œ×™×“×™×.",
    ]
    return "\n".join(lines)

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
        text = ("ðŸ”¥ <b>×œ×™×“ ×—×“×©!</b>\nðŸ‘¤ " + name + "\nðŸ”§ " + service +
                "\nðŸ“ " + location + "\n" +
                ("ðŸ“ž " + phone + "\n" if phone else "") +
                "ðŸ“ " + desc + "\nðŸ”‘ ID: " + rid)
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
            tg_answer(LEADS_TOKEN, cb_id, "××™×Ÿ × ×ª×•×Ÿ", True)
            return jsonify({"ok": True}), 200
        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()
        if action == "lead_open":
            if store: store.update({"status": "open", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "×œ×™×“ ×¤×ª×•×—")
            tg_send(LEADS_TOKEN, chat_id, "âœ… ×œ×™×“ " + rid + " ×¡×•×ž×Ÿ ×›×¤×ª×•×—!")
        elif action == "lead_close":
            if store: store.update({"status": "closed", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "×œ×™×“ × ×¡×’×¨")
            tg_send(LEADS_TOKEN, chat_id, "âŒ ×œ×™×“ " + rid + " × ×¡×’×¨.")
        elif action == "lead_snooze":
            if store: store.update({"status": "snoozed", "updated_at": now}); save_store()
            tg_answer(LEADS_TOKEN, cb_id, "×ª×–×›×•×¨×ª 2×© × ×§×‘×¢×”")
            tg_send(LEADS_TOKEN, chat_id, "â° ×ª×–×›×•×¨×ª ×œ×œ×™×“ " + rid + " ×œ-2 ×©×¢×•×ª.")
        elif action == "lead_improve":
            if not store:
                tg_answer(LEADS_TOKEN, cb_id, "RID ×œ× × ×ž×¦×", True)
                return jsonify({"ok": True}), 200
            prompt = build_lead_prompt(store["data"])
            store.update({"lead_prompt": prompt, "status": "prompt_ready", "updated_at": now})
            save_store()
            tg_answer(LEADS_TOKEN, cb_id, "×¤×¨×•×ž×¤×˜ ×ž×•×›×Ÿ!")
            tg_send(LEADS_TOKEN, chat_id, prompt,
                    [[{"text": "ðŸ”— ×¤×ª×— Lovable", "url": LOVABLE_URL}]])
        else:
            tg_answer(LEADS_TOKEN, cb_id)
        return jsonify({"ok": True}), 200
    except Exception as e:
        logging.exception("[leads_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# HEALTH
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

# START
load_store()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("klik_agent v5.0 - port " + str(port))
    app.run(host="0.0.0.0", port=port, debug=False)
