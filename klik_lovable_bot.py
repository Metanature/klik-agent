#!/usr/bin/env python3
from flask import Flask, request, jsonify
import requests
import logging
import os
import time
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ========= ENV =========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = int(os.environ.get("CHAT_ID", "326460077"))
LOVABLE_URL = os.environ.get(
    "LOVABLE_URL",
    "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325"
).strip()

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""
STORE_FILE = "request_store.json"

# ========= CONST =========
NA = "לא צוין"
HIGH = "גבוהה"
MED = "בינונית"
LOW = "נמוכה"

request_store = {}


# ========= STORE =========
def load_store():
    global request_store
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                request_store = json.load(f)
            logging.info("[store] loaded %s requests", len(request_store))
        except Exception as e:
            logging.error("[store] load failed: %s", e)
            request_store = {}
    else:
        request_store = {}


def save_store():
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(request_store, f, ensure_ascii=False, indent=2)
        logging.info("[store] saved %s requests", len(request_store))
    except Exception as e:
        logging.error("[store] save failed: %s", e)


# ========= TELEGRAM =========
def tg_post(method, payload, timeout=10):
    if not BOT_TOKEN:
        logging.error("[telegram] BOT_TOKEN missing")
        return {"ok": False, "error": "BOT_TOKEN missing"}

    try:
        r = requests.post(f"{BASE_URL}/{method}", json=payload, timeout=timeout)
        res = r.json()
        logging.info("[telegram] %s ok=%s", method, res.get("ok"))
        return res
    except Exception as e:
        logging.error("[telegram] %s failed: %s", method, e)
        return {"ok": False, "error": str(e)}


def tg_send(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    return tg_post("sendMessage", payload)


def tg_edit(chat_id, message_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    return tg_post("editMessageText", payload)


def tg_answer(callback_id, text="OK", show_alert=False):
    payload = {
        "callback_query_id": callback_id,
        "text": text,
        "show_alert": show_alert
    }
    return tg_post("answerCallbackQuery", payload, timeout=5)


# ========= HELPERS =========
def main_keyboard(rid):
    return [
        [
            {"text": "✅ אשר", "callback_data": f"approve:{rid}"},
            {"text": "❌ דחה", "callback_data": f"reject:{rid}"}
        ],
        [
            {"text": "✨ שפר פרומפט", "callback_data": f"improve_prompt:{rid}"},
            {"text": "📊 סטטוס", "callback_data": f"status:{rid}"}
        ],
        [
            {"text": "🚀 שלח ל-Lovable", "callback_data": f"send_to_lovable:{rid}"},
            {"text": "🔗 פתח Lovable", "url": LOVABLE_URL}
        ]
    ]


def small_keyboard(rid):
    return [
        [
            {"text": "🚀 שלח ל-Lovable", "callback_data": f"send_to_lovable:{rid}"},
            {"text": "📊 סטטוס", "callback_data": f"status:{rid}"}
        ],
        [
            {"text": "🔗 Lovable", "url": LOVABLE_URL}
        ]
    ]


def status_keyboard(rid):
    return [
        [
            {"text": "✨ שפר פרומפט", "callback_data": f"improve_prompt:{rid}"}
        ],
        [
            {"text": "🚀 שלח ל-Lovable", "callback_data": f"send_to_lovable:{rid}"}
        ]
    ]


def normalize_action(action):
    action = (action or "").strip().lower()

    aliases = {
        "approve": "approve",
        "ok": "approve",
        "confirm": "approve",

        "reject": "reject",
        "deny": "reject",
        "cancel": "reject",

        "improve_prompt": "improve_prompt",
        "improve": "improve_prompt",
        "prompt": "improve_prompt",

        "status": "status",
        "check_status": "status",

        "send_to_lovable": "send_to_lovable",
        "send": "send_to_lovable",
        "send_lovable": "send_to_lovable",
    }

    return aliases.get(action, action)


def build_improved_prompt(data):
    feature = data.get("feature") or NA
    priority = data.get("priority") or NA
    requested_by = data.get("requested_by") or NA
    details = data.get("details") or NA

    priority_icon = {
        HIGH: "🔴",
        MED: "🟡",
        LOW: "🟢"
    }.get(priority, "🟣")

    lines = [
        "✨ <b>פרומפט משופר ל-Lovable</b>",
        "",
        f"<b>1. מטרה:</b> {feature}",
        "",
        f"<b>2. הבעיה:</b> {details}",
        "",
        "<b>3. מה צריך לשנות:</b>",
        "• UI אם נדרש",
        "• לוגיקה עסקית",
        "• State אם רלוונטי",
        "• לשמור על מה שכבר עובד",
        "",
        "<b>4. דרישות:</b>",
        f"• פיצ'ר: {feature}",
        f"• עדיפות: {priority_icon} {priority}",
        f"• מבקש: {requested_by}",
        f"• פירוט: {details}",
        "",
        "<b>5. מגבלות:</b>",
        "• לא לשנות קוד שלא קשור לבקשה",
        "• לא לשבור פיצ'רים קיימים",
        "• אם צריך שינוי קטן - לבחור בפתרון הפשוט ביותר",
        "",
        "<b>6. תוצאה רצויה:</b>",
        f"הפיצ'ר \"{feature}\" עובד בצורה מלאה, יציבה וברורה למשתמש."
    ]

    return "\n".join(lines)


def make_request_id(data):
    raw_id = (data.get("id") or "").strip()
    if raw_id:
        return raw_id
    return "req_" + str(int(time.time()))


# ========= ROUTES =========
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "klik lovable bot is running"}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "bot": "klik_lovable_bot",
        "version": "3.0",
        "requests_stored": len(request_store),
        "bot_token_exists": bool(BOT_TOKEN)
    }), 200


@app.route("/webhook/lovable", methods=["POST"])
def lovable_webhook():
    try:
        data = request.get_json(silent=True) if request.is_json else request.form.to_dict()

        if not data:
            return jsonify({"status": "error", "message": "empty request"}), 400

        rid = make_request_id(data)
        now = time.time()

        request_store[rid] = {
            "data": data,
            "improved_prompt": None,
            "status": "created",
            "created_at": now,
            "updated_at": now
        }
        save_store()

        feature = data.get("feature") or NA
        priority = data.get("priority") or NA
        requested_by = data.get("requested_by") or NA
        details = data.get("details") or NA

        priority_icon = {
            HIGH: "🔴",
            MED: "🟡",
            LOW: "🟢"
        }.get(priority, "🟣")

        text = (
            "🟣 <b>בקשה חדשה ב-Lovable!</b>\n"
            f"🪄 {feature}\n"
            f"{priority_icon} {priority}\n"
            f"👤 {requested_by}\n"
            f"📝 {details}\n"
            f"🔑 ID: {rid}"
        )

        tg_res = tg_send(CHAT_ID, text, main_keyboard(rid))

        logging.info("[lovable] rid=%s telegram_ok=%s", rid, tg_res.get("ok"))

        return jsonify({
            "status": "ok",
            "request_id": rid,
            "telegram_ok": tg_res.get("ok")
        }), 200

    except Exception as e:
        logging.exception("[lovable] exception")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/webhook/callback", methods=["POST"])
def callback():
    try:
        upd = request.get_json(silent=True) or {}
        logging.info("[cb] RAW UPDATE = %s", upd)

        cb = upd.get("callback_query", {})
        cb_id = cb.get("id", "")
        cb_data = (cb.get("data", "") or "").strip()
        message = cb.get("message", {})
        msg_id = message.get("message_id")
        chat_id = message.get("chat", {}).get("id", CHAT_ID)

        logging.info("[cb] id=%s data=%s", cb_id, cb_data)

        if not cb_data:
            tg_answer(cb_id, "אין נתון בכפתור", show_alert=True)
            return jsonify({"ok": True, "error": "empty_callback_data"}), 200

        if ":" not in cb_data:
            tg_answer(cb_id, "פורמט כפתור לא תקין", show_alert=True)
            return jsonify({"ok": True, "error": "bad_callback_format", "cb_data": cb_data}), 200

        action_raw, rid = cb_data.split(":", 1)
        action = normalize_action(action_raw)
        rid = rid.strip()

        logging.info("[cb] normalized action=%s rid=%s", action, rid)

        store = request_store.get(rid)
        now = time.time()

        if action == "improve_prompt":
            if not store:
                tg_answer(cb_id, f"RID לא נמצא: {rid}", show_alert=True)
                return jsonify({"ok": True, "handler": "improve_prompt", "result": "FAIL_no_rid", "rid": rid}), 200

            improved = build_improved_prompt(store["data"])
            store["improved_prompt"] = improved
            store["status"] = "improved"
            store["updated_at"] = now
            save_store()

            tg_answer(cb_id, "פרומפט שופר")

            result = tg_edit(chat_id, msg_id, improved, keyboard=small_keyboard(rid))

            return jsonify({
                "ok": True,
                "handler": "improve_prompt",
                "rid": rid,
                "edit_ok": result.get("ok")
            }), 200

        elif action == "send_to_lovable":
            if not store:
                tg_answer(cb_id, f"RID לא נמצא: {rid}", show_alert=True)
                return jsonify({"ok": True, "handler": "send_to_lovable", "result": "FAIL_no_rid", "rid": rid}), 200

            prompt = store.get("improved_prompt") or build_improved_prompt(store["data"])
            feature = store["data"].get("feature") or NA

            msg = (
                "🚀 <b>שליחה ל-Lovable</b>\n"
                f"🔑 ID: {rid}\n"
                f"🪄 {feature}\n\n"
                f"{prompt}"
            )

            store["status"] = "sent"
            store["updated_at"] = now
            save_store()

            tg_answer(cb_id, "נשלח")

            result = tg_send(chat_id, msg, keyboard=[
                [{"text": "🔗 Lovable", "url": LOVABLE_URL}],
                [{"text": "📊 סטטוס", "callback_data": f"status:{rid}"}]
            ])

            return jsonify({
                "ok": True,
                "handler": "send_to_lovable",
                "rid": rid,
                "send_ok": result.get("ok")
            }), 200

        elif action == "status":
            if not store:
                tg_answer(cb_id, f"RID לא נמצא: {rid}", show_alert=True)
                return jsonify({"ok": True, "handler": "status", "result": "FAIL_no_rid", "rid": rid}), 200

            feature = store["data"].get("feature") or NA
            status = store.get("status", "unknown")
            has_prompt = "✅ כן" if store.get("improved_prompt") else "❌ עדיין לא"

            msg = (
                "📊 <b>סטטוס</b>\n"
                f"🔑 ID: {rid}\n"
                f"🪄 {feature}\n"
                f"📌 מצב: {status}\n"
                f"✨ פרומפט: {has_prompt}"
            )

            tg_answer(cb_id, "טוען סטטוס")

            result = tg_send(chat_id, msg, keyboard=status_keyboard(rid))

            return jsonify({
                "ok": True,
                "handler": "status",
                "rid": rid,
                "status_value": status,
                "send_ok": result.get("ok")
            }), 200

        elif action == "approve":
            if store:
                store["status"] = "approved"
                store["updated_at"] = now
                save_store()

            tg_answer(cb_id, "אושר")
            tg_send(chat_id, f"✅ בקשה {rid} אושרה!")

            return jsonify({"ok": True, "handler": "approve", "rid": rid}), 200

        elif action == "reject":
            if store:
                store["status"] = "rejected"
                store["updated_at"] = now
                save_store()

            tg_answer(cb_id, "נדחה")
            tg_send(chat_id, f"❌ בקשה {rid} נדחתה.")

            return jsonify({"ok": True, "handler": "reject", "rid": rid}), 200

        else:
            tg_answer(cb_id, f"פעולה לא מזוהה: {action}", show_alert=True)
            return jsonify({
                "ok": True,
                "handler": "unknown",
                "action": action,
                "rid": rid
            }), 200

    except Exception as e:
        logging.exception("[cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ========= START =========
load_store()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"klik_lovable_bot v3.0 running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
