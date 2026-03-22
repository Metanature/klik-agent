#!/usr/bin/env python3
"""
klik_agent v4.0 — Lovable Bot + Leads Bot
Bots: @klik_lovable_bot | @klik_leads_bot
"""
from flask import Flask, request, jsonify
import requests, logging, os, time, json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── ENV ──────────────────────────────────────────────────────────
LOVABLE_TOKEN = os.environ.get("BOT_TOKEN",        "").strip()
LEADS_TOKEN   = os.environ.get("LEADS_BOT_TOKEN",  "").strip()
CHAT_ID       = int(os.environ.get("CHAT_ID",       "326460077"))
LOVABLE_URL   = os.environ.get("LOVABLE_URL",
    "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325").strip()

# ── CONST ─────────────────────────────────────────────────────────
NA   = "\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df"
HIGH = "\u05d2\u05d1\u05d5\u05d4\u05d4"
MED  = "\u05d1\u05d9\u05e0\u05d5\u05e0\u05d9\u05ea"
LOW  = "\u05e0\u05de\u05d5\u05db\u05d4"
PRIORITY_ICON = {HIGH: "\ud83d\udd34", MED: "\ud83d\udfe1", LOW: "\ud83d\udfe2"}

# ── STORE ─────────────────────────────────────────────────────────
STORE_FILE = "request_store.json"
request_store = {}

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
            json.dump(request_store, f, ensure_ascii=True, indent=2)
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

# ══════════════════════════════════════════════════════════════════
#  LOVABLE BOT — premium Lovable request flow
# ══════════════════════════════════════════════════════════════════

def lovable_keyboard(rid):
    return [
        [{"text": "\u2705 \u05d0\u05e9\u05e8",  "callback_data": "approve:" + rid},
         {"text": "\u274c \u05d3\u05d7\u05d4",   "callback_data": "reject:"  + rid}],
        [{"text": "\u2728 \u05e9\u05e4\u05e8 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8",
          "callback_data": "improve_prompt:" + rid},
         {"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1",
          "callback_data": "status:" + rid}],
        [{"text": "\ud83d\ude80 \u05e9\u05dc\u05d7 \u05dc-Lovable",
          "callback_data": "send_to_lovable:" + rid},
         {"text": "\ud83d\udd17 \u05e4\u05ea\u05d7 Lovable", "url": LOVABLE_URL}],
    ]

def lovable_small_kb(rid):
    return [
        [{"text": "\ud83d\ude80 \u05e9\u05dc\u05d7 \u05dc-Lovable",
          "callback_data": "send_to_lovable:" + rid},
         {"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1",
          "callback_data": "status:" + rid}],
        [{"text": "\ud83d\udd17 Lovable", "url": LOVABLE_URL}],
    ]


def build_lovable_prompt(data):
    """Premium 6-section Lovable prompt."""
    feature  = data.get("feature")      or NA
    priority = data.get("priority")     or NA
    req_by   = data.get("requested_by") or NA
    details  = data.get("details")      or NA
    pe       = PRIORITY_ICON.get(priority, "\ud83d\udfe3")
    return "\n".join([
        "\u2728 <b>\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05e4\u05e8\u05de\u05d9\u05d5\u05dd \u05dc-Lovable</b>",
        "",
        "<b>1\ufe0f\u20e3 \u05de\u05d8\u05e8\u05d4</b>",
        "\u05dc\u05d4\u05d8\u05de\u05d9\u05e2 \u05d0\u05ea \u05d4\u05e4\u05d9\u05e6\u05f3\u05e8: <b>" + feature + "</b>",
        "\u05d1\u05e6\u05d5\u05e8\u05d4 \u05de\u05dc\u05d0\u05d4, \u05d9\u05e6\u05d9\u05d1\u05d4 \u05d5\u05e0\u05e7\u05d9\u05d4 \u05dc\u05de\u05e9\u05ea\u05de\u05e9.",
        "",
        "<b>2\ufe0f\u20e3 \u05d4\u05d1\u05e2\u05d9\u05d4</b>",
        details,
        "",
        "<b>3\ufe0f\u20e3 \u05de\u05d4 \u05e6\u05e8\u05d9\u05da \u05dc\u05e9\u05e0\u05d5\u05ea</b>",
        "\u2022 \u05e2\u05d3\u05db\u05df \u05d0\u05ea \u05d4-UI \u05d0\u05dd \u05e0\u05d3\u05e8\u05e9 — \u05dc\u05e9\u05de\u05d5\u05e8 \u05e2\u05dc \u05e7\u05d5\u05d4\u05e8\u05e0\u05d8\u05d9\u05d5\u05ea \u05d5\u05d9\u05d6\u05d5\u05d0\u05dc\u05d9\u05ea",
        "\u2022 \u05e2\u05d3\u05db\u05df \u05dc\u05d5\u05d2\u05d9\u05e7\u05d4 \u05e2\u05e1\u05e7\u05d9\u05ea \u05d1\u05dc\u05d1\u05d3 \u05d1\u05e0\u05d5\u05d2\u05e2 \u05dc\u05e4\u05d9\u05e6\u05f3\u05e8",
        "\u2022 \u05e2\u05d3\u05db\u05df State \u05d0\u05dd \u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9 — \u05dc\u05d5\u05d5\u05d3\u05d0 \u05e9\u05d4\u05e0\u05ea\u05d5\u05e0\u05d9\u05dd \u05e0\u05e9\u05de\u05e8\u05d9\u05dd",
        "\u2022 \u05d0\u05e4\u05e1 \u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd \u05e9\u05dc\u05d0 \u05e7\u05e9\u05d5\u05e8\u05d9\u05dd \u05dc\u05d1\u05e7\u05e9\u05d4",
        "",
        "<b>4\ufe0f\u20e3 \u05d3\u05e8\u05d9\u05e9\u05d5\u05ea \u05de\u05d3\u05d5\u05d9\u05e7\u05d5\u05ea</b>",
        "\u2022 \u05e4\u05d9\u05e6\u05f3\u05e8: " + feature,
        "\u2022 \u05e2\u05d3\u05d9\u05e4\u05d5\u05ea: " + pe + " " + priority,
        "\u2022 \u05de\u05d1\u05e7\u05e9: " + req_by,
        "\u2022 \u05e4\u05d9\u05e8\u05d5\u05d8: " + details,
        "",
        "<b>5\ufe0f\u20e3 \u05de\u05d2\u05d1\u05dc\u05d5\u05ea</b>",
        "\u2022 \u05dc\u05d0 \u05dc\u05e9\u05e0\u05d5\u05ea \u05e7\u05d5\u05d3 \u05e9\u05dc\u05d0 \u05e7\u05e9\u05d5\u05e8 \u05dc\u05d1\u05e7\u05e9\u05d4 \u05d6\u05d5",
        "\u2022 \u05dc\u05d0 \u05dc\u05e9\u05d1\u05d5\u05e8 \u05e4\u05d9\u05e6\u05f3\u05e8\u05d9\u05dd \u05e7\u05d9\u05d9\u05de\u05d9\u05dd",
        "\u2022 \u05d0\u05dd \u05e6\u05e8\u05d9\u05da \u05e9\u05d9\u05e0\u05d5\u05d9 DB \u2014 \u05dc\u05ea\u05d0\u05dd \u05e7\u05d5\u05d3\u05dd \u05d5\u05dc\u05d0 \u05dc\u05e9\u05d1\u05d5\u05e8",
        "\u2022 \u05dc\u05d0 \u05dc\u05d4\u05d5\u05e1\u05d9\u05e3 \u05d7\u05d1\u05d9\u05dc\u05d5\u05ea \u05dc\u05dc\u05d0 \u05d0\u05d9\u05e9\u05d5\u05e8",
        "",
        "<b>6\ufe0f\u20e3 \u05ea\u05d5\u05e6\u05d0\u05d4 \u05e8\u05e6\u05d5\u05d9\u05d4</b>",
        "\u05d4\u05e4\u05d9\u05e6\u05f3\u05e8 \"" + feature + "\" \u05e2\u05d5\u05d1\u05d3 \u05d1\u05de\u05dc\u05d5\u05d0\u05d5 \u05d5\u05d1\u05e6\u05d5\u05e8\u05d4 \u05d9\u05e6\u05d9\u05d1\u05d4.",
        "\u05e0\u05d1\u05d3\u05e7 \u05db\u05dc \u05de\u05e7\u05e8\u05d4 \u05e7\u05e6\u05d4 \u05dc\u05e4\u05e0\u05d9 \u05e1\u05d9\u05d5\u05dd.",
    ])


@app.route("/webhook/lovable", methods=["POST"])
def lovable_webhook():
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "empty"}), 400

        rid  = make_rid(data, "req")
        now  = time.time()
        request_store[rid] = {
            "type": "lovable", "data": data,
            "improved_prompt": None, "status": "created",
            "created_at": now, "updated_at": now,
        }
        save_store()

        feature  = data.get("feature")      or NA
        priority = data.get("priority")     or NA
        req_by   = data.get("requested_by") or NA
        details  = data.get("details")      or NA
        pe       = PRIORITY_ICON.get(priority, "\ud83d\udfe3")

        text = (
            "\ud83d\udfe3 <b>\u05d1\u05e7\u05e9\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05d1-Lovable!</b>\n"
            + "\ud83e\ude84 " + feature + "\n"
            + pe + " " + priority + "\n"
            + "\ud83d\udc64 " + req_by + "\n"
            + "\ud83d\udcdd " + details + "\n"
            + "\ud83d\udd11 ID: " + rid
        )
        res = tg_send(LOVABLE_TOKEN, CHAT_ID, text, lovable_keyboard(rid))
        logging.info("[lovable] rid=%s ok=%s", rid, res.get("ok"))
        return jsonify({"status": "ok", "request_id": rid, "telegram_ok": res.get("ok")}), 200
    except Exception as e:
        logging.exception("[lovable] exception")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/webhook/callback", methods=["POST"])
def lovable_callback():
    try:
        upd    = request.get_json(silent=True) or {}
        cb     = upd.get("callback_query", {})
        cb_id  = cb.get("id", "")
        cb_data= (cb.get("data") or "").strip()
        msg    = cb.get("message", {})
        msg_id = msg.get("message_id")
        chat_id= msg.get("chat", {}).get("id", CHAT_ID)

        logging.info("[lovable_cb] data=%s", cb_data)
        if not cb_data or ":" not in cb_data:
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05d0\u05d9\u05df \u05e0\u05ea\u05d5\u05df", True)
            return jsonify({"ok": True}), 200

        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()

        if action == "improve_prompt":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0", True)
                return jsonify({"ok": True, "handler": "improve_prompt", "result": "no_rid"}), 200
            prompt = build_lovable_prompt(store["data"])
            store.update({"improved_prompt": prompt, "status": "improved", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05e9\u05d5\u05e4\u05e8!")
            result = tg_edit(LOVABLE_TOKEN, chat_id, msg_id, prompt, lovable_small_kb(rid))
            return jsonify({"ok": True, "handler": "improve_prompt", "rid": rid,
                            "edit_ok": result.get("ok")}), 200

        elif action == "send_to_lovable":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0", True)
                return jsonify({"ok": True}), 200
            prompt  = store.get("improved_prompt") or build_lovable_prompt(store["data"])
            feature = store["data"].get("feature") or NA
            msg_text= (
                "\ud83d\ude80 <b>\u05e9\u05dc\u05d9\u05d7\u05d4 \u05dc-Lovable</b>\n"
                + "\ud83d\udd11 ID: " + rid + "\n"
                + "\ud83e\ude84 " + feature + "\n\n"
                + prompt
            )
            store.update({"status": "sent", "updated_at": now})
            save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05e0\u05e9\u05dc\u05d7!")
            res = tg_send(LOVABLE_TOKEN, chat_id, msg_text, [
                [{"text": "\ud83d\udd17 \u05e4\u05ea\u05d7 Lovable", "url": LOVABLE_URL}],
                [{"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1", "callback_data": "status:" + rid}],
            ])
            return jsonify({"ok": True, "handler": "send_to_lovable", "rid": rid,
                            "send_ok": res.get("ok")}), 200

        elif action == "status":
            if not store:
                tg_answer(LOVABLE_TOKEN, cb_id, "RID \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0", True)
                return jsonify({"ok": True}), 200
            feature  = store["data"].get("feature") or NA
            status   = store.get("status", "unknown")
            has_p    = "\u2705 \u05db\u05df" if store.get("improved_prompt") else "\u274c \u05d8\u05e8\u05dd"
            msg_text = (
                "\ud83d\udcca <b>\u05e1\u05d8\u05d8\u05d5\u05e1</b>\n"
                + "\ud83d\udd11 " + rid + "\n"
                + "\ud83e\ude84 " + feature + "\n"
                + "\ud83d\udccc \u05de\u05e6\u05d1: " + status + "\n"
                + "\u2728 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8: " + has_p
            )
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05e1\u05d8\u05d8\u05d5\u05e1 \u05d8\u05e2\u05d5\u05df")
            tg_send(LOVABLE_TOKEN, chat_id, msg_text, lovable_small_kb(rid))
            return jsonify({"ok": True, "handler": "status", "rid": rid}), 200

        elif action == "approve":
            if store:
                store.update({"status": "approved", "updated_at": now})
                save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05d0\u05d5\u05e9\u05e8!")
            tg_send(LOVABLE_TOKEN, chat_id, "\u2705 \u05d1\u05e7\u05e9\u05d4 " + rid + " \u05d0\u05d5\u05e9\u05e8\u05d4!")
            return jsonify({"ok": True, "handler": "approve", "rid": rid}), 200

        elif action == "reject":
            if store:
                store.update({"status": "rejected", "updated_at": now})
                save_store()
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05e0\u05d3\u05d7\u05d4")
            tg_send(LOVABLE_TOKEN, chat_id, "\u274c \u05d1\u05e7\u05e9\u05d4 " + rid + " \u05e0\u05d3\u05d7\u05ea\u05d4.")
            return jsonify({"ok": True, "handler": "reject", "rid": rid}), 200

        else:
            tg_answer(LOVABLE_TOKEN, cb_id, "\u05e4\u05e2\u05d5\u05dc\u05d4 \u05dc\u05d0 \u05de\u05d5\u05db\u05e8\u05ea: " + action)
            return jsonify({"ok": True, "handler": "unknown", "action": action}), 200

    except Exception as e:
        logging.exception("[lovable_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ══════════════════════════════════════════════════════════════════
#  LEADS BOT — premium lead management flow
# ══════════════════════════════════════════════════════════════════

def leads_keyboard(rid, phone=""):
    phone_clean = clean_phone(phone) if phone else ""
    kb = []
    if phone_clean:
        kb.append([
            {"text": "\ud83d\udcde \u05d4\u05ea\u05e7\u05e9\u05e8 \u05e2\u05db\u05e9\u05d9\u05d5",
             "url": "https://wa.me/" + phone_clean + "?text=\u05e9\u05dc\u05d5\u05dd, \u05d0\u05e0\u05d9 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05dc\u05d9\u05e7"},
            {"text": "\ud83d\udcac WhatsApp",
             "url": "https://wa.me/" + phone_clean},
        ])
    kb.append([
        {"text": "\u2705 \u05e4\u05ea\u05d5\u05d7", "callback_data": "lead_open:"  + rid},
        {"text": "\u274c \u05e1\u05d2\u05d5\u05e8", "callback_data": "lead_close:" + rid},
    ])
    kb.append([
        {"text": "\u23f0 \u05ea\u05d6\u05db\u05d5\u05e8\u05ea 2\u05e9",
         "callback_data": "lead_snooze:" + rid},
        {"text": "\u2728 \u05e9\u05e4\u05e8 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05dc-Lovable",
         "callback_data": "lead_improve:" + rid},
    ])
    return kb


def build_lead_prompt(data):
    """Premium Lovable prompt based on incoming lead."""
    name        = data.get("name")        or NA
    service     = data.get("service")     or NA
    location    = data.get("location")    or NA
    description = data.get("description") or NA
    return "\n".join([
        "\u2728 <b>\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05e4\u05e8\u05de\u05d9\u05d5\u05dd \u05dc-Lovable — \u05e9\u05d9\u05e4\u05d5\u05e8 \u05e9\u05d9\u05e8\u05d5\u05ea</b>",
        "",
        "<b>1\ufe0f\u20e3 \u05de\u05d8\u05e8\u05d4</b>",
        "\u05dc\u05e9\u05e4\u05e8 \u05d0\u05ea \u05d3\u05e3 \u05d4\u05e9\u05d9\u05e8\u05d5\u05ea <b>" + service + "</b> \u05db\u05d3\u05d9 \u05dc\u05d4\u05d2\u05d3\u05d9\u05dc \u05d4\u05de\u05e8\u05ea \u05dc\u05d9\u05d3\u05d9\u05dd \u05de\u05d0\u05d6\u05d5\u05e8 " + location + ".",
        "",
        "<b>2\ufe0f\u20e3 \u05d4\u05e7\u05e9\u05e8</b>",
        "\u05dc\u05d9\u05d3 \u05d7\u05d9 \u05e0\u05db\u05e0\u05e1: " + name + " \u05de" + location + " \u05d1\u05d9\u05e7\u05e9 " + service + ".",
        "\u05d4\u05e6\u05d5\u05e8\u05da: " + description,
        "",
        "<b>3\ufe0f\u20e3 \u05de\u05d4 \u05dc\u05e9\u05e4\u05e8</b>",
        "\u2022 \u05d3\u05e3 \u05e9\u05d9\u05e8\u05d5\u05ea " + service + " \u05e2\u05dd \u05d4\u05e1\u05d1\u05e8 \u05e6\u05dc\u05d5\u05dc\u05d4 \u05d5\u05ea\u05de\u05d5\u05e0\u05d5\u05ea \u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9\u05d5\u05ea",
        "\u2022 CTA \u05d1\u05e8\u05d5\u05e8 \u05dc\u05d5\u05d5\u05d0\u05d8\u05e1\u05d0\u05e4/\u05d8\u05dc\u05e4\u05d5\u05df \u05e2\u05dd \u05de\u05e1\u05e4\u05e8 \u05d4\u05d8\u05dc\u05e4\u05d5\u05df",
        "\u2022 \u05d8\u05d5\u05e4\u05e1 \u05d1\u05d9\u05e6\u05d5\u05e2 \u05de\u05d4\u05d9\u05e8 \u05e2\u05dd \u05e9\u05d3\u05d5\u05ea: \u05e9\u05dd / \u05d8\u05dc\u05e4\u05d5\u05df / \u05de\u05d9\u05e7\u05d5\u05dd / \u05e9\u05d9\u05e8\u05d5\u05ea",
        "\u2022 \u05e1\u05e7\u05e9\u05ea \u05e6\u05e4\u05e8\u05d3\u05d9\u05ea \u05dc-trust \u05e2\u05dd \u05e8\u05d9\u05e9\u05d5\u05de\u05d5\u05ea / \u05e4\u05e8\u05d5\u05d9\u05e7\u05d8\u05d9\u05dd",
        "",
        "<b>4\ufe0f\u20e3 \u05d3\u05e8\u05d9\u05e9\u05d5\u05ea</b>",
        "\u2022 \u05e9\u05d9\u05e8\u05d5\u05ea: " + service,
        "\u2022 \u05d0\u05d6\u05d5\u05e8: " + location,
        "\u2022 \u05d8\u05d5\u05e4\u05e1 \u05d7\u05d5\u05d6\u05e8 \u05dc\u05d9\u05d3 \u05e2\u05dd \u05de\u05e2\u05e7\u05d1 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9 \u05dc-WhatsApp",
        "\u2022 \u05e2\u05d9\u05e6\u05d5\u05d1 \u05e8\u05e1\u05e4\u05d5\u05e0\u05e1\u05d9\u05d1\u05d9 \u05d5\u05de\u05d4\u05d9\u05e8",
        "",
        "<b>5\ufe0f\u20e3 \u05de\u05d2\u05d1\u05dc\u05d5\u05ea</b>",
        "\u2022 \u05dc\u05d0 \u05dc\u05e9\u05e0\u05d5\u05ea \u05d6\u05e8\u05d9\u05de\u05ea \u05e0\u05d9\u05d5\u05d5\u05d8 \u05e7\u05d9\u05d9\u05de\u05ea",
        "\u2022 \u05dc\u05e9\u05de\u05d5\u05e8 \u05e2\u05dc \u05de\u05d9\u05ea\u05d5\u05d2 \u05e2\u05e7\u05d1\u05d9",
        "\u2022 \u05dc\u05d0 \u05dc\u05d4\u05d5\u05e1\u05d9\u05e3 \u05e4\u05d5\u05e0\u05e7\u05e6\u05d9\u05d5\u05e0\u05dc\u05d9\u05d5\u05ea \u05dc\u05dc\u05d0 \u05d0\u05d9\u05e9\u05d5\u05e8",
        "",
        "<b>6\ufe0f\u20e3 \u05ea\u05d5\u05e6\u05d0\u05d4 \u05e8\u05e6\u05d5\u05d9\u05d4</b>",
        "\u05d3\u05e3 " + service + " \u05d1" + location + " \u05de\u05de\u05d9\u05e8 \u05dc\u05d9\u05d3\u05d9\u05dd \u05d1\u05d0\u05d5\u05e4\u05df \u05de\u05e7\u05e1\u05d9\u05de\u05dc\u05d9 \u05d5\u05e0\u05d5\u05ea\u05df \u05d1\u05d8\u05d7\u05d5\u05df.",
    ])


@app.route("/webhook/leads", methods=["POST"])
def leads_webhook():
    try:
        data = request.get_json(silent=True) or request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "empty"}), 400

        rid  = make_rid(data, "lead")
        now  = time.time()
        phone = data.get("phone", "")
        request_store[rid] = {
            "type": "lead", "data": data,
            "lead_prompt": None, "status": "new",
            "created_at": now, "updated_at": now,
        }
        save_store()

        name     = data.get("name")        or NA
        service  = data.get("service")     or NA
        location = data.get("location")    or NA
        desc     = data.get("description") or NA

        text = (
            "\ud83d\udd25 <b>\u05dc\u05d9\u05d3 \u05d7\u05d3\u05e9!</b>\n"
            + "\ud83d\udc64 " + name    + "\n"
            + "\ud83d\udd27 " + service + "\n"
            + "\ud83d\udccd " + location + "\n"
            + ("\ud83d\udcde " + phone + "\n" if phone else "")
            + "\ud83d\udcdd " + desc    + "\n"
            + "\ud83d\udd11 ID: " + rid
        )
        res = tg_send(LEADS_TOKEN, CHAT_ID, text, leads_keyboard(rid, phone))
        logging.info("[leads] rid=%s ok=%s", rid, res.get("ok"))
        return jsonify({"status": "ok", "request_id": rid, "telegram_ok": res.get("ok")}), 200
    except Exception as e:
        logging.exception("[leads] exception")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/webhook/callback/leads", methods=["POST"])
def leads_callback():
    try:
        upd    = request.get_json(silent=True) or {}
        cb     = upd.get("callback_query", {})
        cb_id  = cb.get("id", "")
        cb_data= (cb.get("data") or "").strip()
        msg    = cb.get("message", {})
        msg_id = msg.get("message_id")
        chat_id= msg.get("chat", {}).get("id", CHAT_ID)

        logging.info("[leads_cb] data=%s", cb_data)
        if not cb_data or ":" not in cb_data:
            tg_answer(LEADS_TOKEN, cb_id, "\u05d0\u05d9\u05df \u05e0\u05ea\u05d5\u05df", True)
            return jsonify({"ok": True}), 200

        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid.strip())
        now   = time.time()

        if action == "lead_open":
            if store:
                store.update({"status": "open", "updated_at": now})
                save_store()
            tg_answer(LEADS_TOKEN, cb_id, "\u05dc\u05d9\u05d3 \u05e4\u05ea\u05d5\u05d7")
            tg_send(LEADS_TOKEN, chat_id,
                    "\u2705 \u05dc\u05d9\u05d3 " + rid + " \u05e1\u05d5\u05de\u05df \u05db\u05e4\u05ea\u05d5\u05d7!")
            return jsonify({"ok": True, "handler": "lead_open", "rid": rid}), 200

        elif action == "lead_close":
            if store:
                store.update({"status": "closed", "updated_at": now})
                save_store()
            tg_answer(LEADS_TOKEN, cb_id, "\u05dc\u05d9\u05d3 \u05e0\u05e1\u05d2\u05e8")
            tg_send(LEADS_TOKEN, chat_id,
                    "\u274c \u05dc\u05d9\u05d3 " + rid + " \u05e0\u05e1\u05d2\u05e8.")
            return jsonify({"ok": True, "handler": "lead_close", "rid": rid}), 200

        elif action == "lead_snooze":
            if store:
                store.update({"status": "snoozed", "updated_at": now})
                save_store()
            tg_answer(LEADS_TOKEN, cb_id, "\u05ea\u05d6\u05db\u05d5\u05e8\u05ea 2\u05e9 \u05e0\u05e7\u05d1\u05e2\u05d4")
            tg_send(LEADS_TOKEN, chat_id,
                    "\u23f0 \u05ea\u05d6\u05db\u05d5\u05e8\u05ea \u05dc\u05dc\u05d9\u05d3 " + rid
                    + " \u05e0\u05e7\u05d1\u05e2\u05d4 \u05dc-2 \u05e9\u05e2\u05d5\u05ea.")
            return jsonify({"ok": True, "handler": "lead_snooze", "rid": rid}), 200

        elif action == "lead_improve":
            if not store:
                tg_answer(LEADS_TOKEN, cb_id, "RID \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0", True)
                return jsonify({"ok": True, "handler": "lead_improve", "result": "no_rid"}), 200
            prompt = build_lead_prompt(store["data"])
            store.update({"lead_prompt": prompt, "status": "prompt_ready", "updated_at": now})
            save_store()
            tg_answer(LEADS_TOKEN, cb_id, "\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05de\u05d5\u05db\u05df!")
            res = tg_send(LEADS_TOKEN, chat_id, prompt, [
                [{"text": "\ud83d\udd17 \u05e4\u05ea\u05d7 Lovable", "url": LOVABLE_URL}],
            ])
            return jsonify({"ok": True, "handler": "lead_improve", "rid": rid,
                            "send_ok": res.get("ok")}), 200

        else:
            tg_answer(LEADS_TOKEN, cb_id, "\u05e4\u05e2\u05d5\u05dc\u05d4 \u05dc\u05d0 \u05de\u05d5\u05db\u05e8\u05ea: " + action)
            return jsonify({"ok": True, "handler": "unknown", "action": action}), 200

    except Exception as e:
        logging.exception("[leads_cb] exception")
        return jsonify({"ok": True, "error": str(e)}), 200


# ── HEALTH ────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({"ok": True, "message": "klik_agent v4.0 running"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "version": "4.0",
        "lovable_token": bool(LOVABLE_TOKEN),
        "leads_token":   bool(LEADS_TOKEN),
        "requests":      len(request_store),
    }), 200


# ── START ─────────────────────────────────────────────────────────
load_store()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("klik_agent v4.0 — port " + str(port))
    app.run(host="0.0.0.0", port=port, debug=False)
