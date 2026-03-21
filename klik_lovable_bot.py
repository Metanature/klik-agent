#!/usr/bin/env python3
"""
Klik Multi-Bot Agent v3.1 \u2014 5 Bots + Inline Keyboards + Callback Handling
"""
from flask import Flask, request, jsonify
import requests, json, logging, os          # \u2190 \u05ea\u05d9\u05e7\u05d5\u05df 1: \u05e0\u05d5\u05e1\u05e3 os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CHAT_ID = 326460077
BOTS = {
    "leads":       {"token": "8643090938:AAGo55jGaZFlzKJm63_QPcpQPp2Ow5p5vFw", "name": "\u05dc\u05d9\u05d3\u05d9\u05dd \u05e0\u05db\u05e0\u05e1\u05d9\u05dd"},
    "bugs":        {"token": "8785442399:AAFTsUKKe55l31yjfeAs_-g2TRxYqtvWdp8", "name": "\u05ea\u05e7\u05dc\u05d5\u05ea \u05d8\u05db\u05e0\u05d9\u05d5\u05ea"},
    "lovable":     {"token": "8690987639:AAH83slPs_j_H7pGSfpeGWTWirCsiJHi7Ks", "name": "\u05d1\u05e7\u05e9\u05d5\u05ea Lovable"},
    "matchmaking": {"token": "8622414362:AAFYG8Qk_5oQYTmOdxx6CccMaDhh2fpTZmk", "name": "\u05d4\u05e6\u05e2\u05d5\u05ea \u05dc\u05e9\u05d9\u05d3\u05d5\u05db\u05d9\u05dd"},
    "health":      {"token": "8706328171:AAHGB5bLM1oe4ZdqkPR4AEk4ld_kp6jhMe8", "name": "\u05d3\u05d9\u05d5\u05d5\u05d7 \u05e2\u05dc \u05ea\u05e7\u05dc\u05d4"},
}
LOVABLE_URL = "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325"


def clean_phone(phone):
    digits = phone.replace("-","").replace(" ","").replace("+","")
    if digits.startswith("972"):
        return digits
    return "972" + digits.lstrip("0")


def tg(token, chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json=payload, timeout=10)
    return r.json().get("ok", False)


def answer_callback(token, callback_id, text="\u2705"):
    requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                  json={"callback_query_id": callback_id, "text": text}, timeout=5)


def fmt_lead(d):
    lid   = d.get("id", "")
    phone = clean_phone(d.get("phone", "0500000000"))
    text = (
        "\u1f525 <b>\u05dc\u05e7\u05d5\u05d7 \u05d7\u05d3\u05e9!</b>\n"
        f"\u1f464 \u05e9\u05dd: {d.get('name','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f527 \u05e9\u05d9\u05e8\u05d5\u05ea: {d.get('service','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4cd \u05de\u05d9\u05e7\u05d5\u05dd: {d.get('location','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4de \u05d8\u05dc\u05e4\u05d5\u05df: {d.get('phone','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4dd \u05ea\u05d9\u05d0\u05d5\u05e8: {d.get('description','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}"
    )
    kb = [
        [
            {"text": "\u1f4de \u05d4\u05ea\u05e7\u05e9\u05e8 \u05e2\u05db\u05e9\u05d9\u05d5", "url": f"https://wa.me/{phone}?text=\u05e9\u05dc\u05d5\u05dd"},
            {"text": "\u1f4ac WhatsApp",     "url": f"https://wa.me/{phone}"},
        ],
        [
            {"text": "\u274c \u05e1\u05d2\u05d5\u05e8 \u05dc\u05d9\u05d3",   "callback_data": f"close_lead:{lid}"},
            {"text": "\u23f0 \u05ea\u05d6\u05db\u05d5\u05e8\u05ea 2\u05e9", "callback_data": f"snooze_lead:{lid}"},
        ],
    ]
    return text, kb


def fmt_bug(d):
    bid = d.get("id", "")
    sev = {"\u05d2\u05d1\u05d5\u05d4\u05d4": "\u1f534", "\u05d1\u05d9\u05e0\u05d5\u05e0\u05d9\u05ea": "\u1f7e1", "\u05e0\u05de\u05d5\u05db\u05d4": "\u1f7e2"}.get(d.get("severity",""), "\u1f534")
    text = (
        "\u1f534 <b>\u05ea\u05e7\u05dc\u05d4 \u05d7\u05d3\u05e9\u05d4!</b>\n"
        f"\u1f4cc \u05e0\u05d5\u05e9\u05d0: {d.get('title','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"{sev} \u05d7\u05d5\u05de\u05e8\u05d4: {d.get('severity','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f464 \u05de\u05d3\u05d5\u05d5\u05d7: {d.get('reported_by','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4dd \u05ea\u05d9\u05d0\u05d5\u05e8: {d.get('description','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f517 \u05e7\u05d9\u05e9\u05d5\u05e8: {d.get('url','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}"
    )
    kb = [
        [
            {"text": "\u2705 \u05d0\u05e9\u05e8 \u05d5\u05ea\u05e7\u05df",      "callback_data": f"approve_bug:{bid}"},
            {"text": "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd",          "callback_data": f"complete_bug:{bid}"},
        ],
        [
            {"text": "\u1f513 \u05e4\u05ea\u05d7 \u05d1-Lovable", "url": LOVABLE_URL},
            {"text": "\u1f680 \u05d4\u05e8\u05e5 \u05e2\u05db\u05e9\u05d9\u05d5",     "callback_data": f"run_fix:{bid}"},
        ],
        [
            {"text": "\u1f50d \u05e1\u05d8\u05d8\u05d5\u05e1",         "callback_data": f"status_bug:{bid}"},
            {"text": "\u2728 \u05e9\u05e4\u05e8 \u05e2\u05d5\u05d3",        "callback_data": f"improve_bug:{bid}"},
        ],
    ]
    return text, kb


def fmt_lovable(d):
    rid = d.get("id", "")
    pri = {"\u05d2\u05d1\u05d5\u05d4\u05d4": "\u1f534", "\u05d1\u05d9\u05e0\u05d5\u05e0\u05d9\u05ea": "\u1f7e1", "\u05e0\u05de\u05d5\u05db\u05d4": "\u1f7e2"}.get(d.get("priority",""), "\u1f535")
    details = d.get("details","")
    text = (
        "\u1f535 <b>\u05d1\u05e7\u05e9\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05d1-Lovable!</b>\n"
        f"\u1fa84 \u05e4\u05d9\u05e6'\u05e8: {d.get('feature','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"{pri} \u05e2\u05d3\u05d9\u05e4\u05d5\u05ea: {d.get('priority','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f464 \u05de\u05d1\u05e7\u05e9: {d.get('requested_by','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4dd \u05e4\u05e8\u05d8\u05d9\u05dd: {details}"
    )
    kb = [
        [
            {"text": "\u2705 \u05d0\u05e9\u05e8",            "callback_data": f"approve_request:{rid}"},
            {"text": "\u274c \u05d3\u05d7\u05d4",            "callback_data": f"reject_request:{rid}"},
        ],
        [
            {"text": "\u1f680 \u05e9\u05dc\u05d7 \u05dc-Lovable", "url": LOVABLE_URL},
            {"text": "\u2728 \u05e9\u05e4\u05e8 \u05e2\u05d5\u05d3",        "callback_data": f"improve_request:{rid}"},
        ],
    ]
    return text, kb


def fmt_matchmaking(d):
    mid = d.get("id", "")
    text = (
        "\u1f7e3 <b>\u05d4\u05e6\u05e2\u05ea \u05e9\u05d9\u05d3\u05d5\u05da \u05d7\u05d3\u05e9\u05d4!</b>\n"
        f"\u1f464 \u05e9\u05dd: {d.get('name','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f382 \u05d2\u05d9\u05dc: {d.get('age','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4cd \u05de\u05d9\u05e7\u05d5\u05dd: {d.get('location','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4de \u05d8\u05dc\u05e4\u05d5\u05df: {d.get('phone','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4dd \u05ea\u05d9\u05d0\u05d5\u05e8: {d.get('description','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}"
    )
    kb = [
        [
            {"text": "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd",          "callback_data": f"complete_match:{mid}"},
            {"text": "\u1f50d \u05e1\u05d8\u05d8\u05d5\u05e1",         "callback_data": f"status_match:{mid}"},
        ],
        [
            {"text": "\u1f513 \u05e4\u05ea\u05d7 \u05d1-Lovable", "url": LOVABLE_URL},
            {"text": "\u2728 \u05e9\u05e4\u05e8 \u05e4\u05e8\u05d5\u05e4\u05d9\u05dc",    "url": f"{LOVABLE_URL}?message=\u05e9\u05e4\u05e8+\u05e4\u05e8\u05d5\u05e4\u05d9\u05dc:{d.get('name','')}"},
        ],
    ]
    return text, kb


def fmt_health(d):
    hid = d.get("id", "")
    text = (
        "\u1fa7a <b>\u05d3\u05d9\u05d5\u05d5\u05d7 \u05e2\u05dc \u05ea\u05e7\u05dc\u05d4!</b>\n"
        f"\u1f4cc \u05db\u05d5\u05ea\u05e8\u05ea: {d.get('title','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f464 \u05de\u05d3\u05d5\u05d5\u05d7: {d.get('reported_by','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u1f4dd \u05ea\u05d9\u05d0\u05d5\u05e8: {d.get('description','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}\n"
        f"\u26a0\ufe0f \u05d3\u05d7\u05d9\u05e4\u05d5\u05ea: {d.get('urgency','\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df')}"
    )
    kb = [
        [
            {"text": "\u2705 \u05d0\u05d9\u05e9\u05e8\u05ea\u05d9",         "callback_data": f"approve_health:{hid}"},
            {"text": "\u1f513 \u05e4\u05ea\u05d7 \u05d1-Lovable", "url": LOVABLE_URL},
        ],
        [
            {"text": "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd",          "callback_data": f"complete_health:{hid}"},
            {"text": "\u1f4ca \u05e1\u05d8\u05d8\u05d5\u05e1",         "callback_data": f"status_health:{hid}"},
        ],
    ]
    return text, kb


CALLBACK_RESPONSES = {
    "close_lead":       ("\u2705 \u05d4\u05dc\u05d9\u05d3 \u05e0\u05e1\u05d2\u05e8 \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4", "\u274c \u05dc\u05d9\u05d3 \u05e0\u05e1\u05d2\u05e8"),
    "snooze_lead":      ("\u23f0 \u05ea\u05d6\u05db\u05d5\u05e8\u05ea \u05e0\u05e7\u05d1\u05e2\u05d4 \u05dc\u05e2\u05d5\u05d3 2 \u05e9\u05e2\u05d5\u05ea", "\u23f0 \u05ea\u05d6\u05db\u05d5\u05e8\u05ea"),
    "approve_bug":      ("\u2705 \u05d4\u05ea\u05e7\u05dc\u05d4 \u05d0\u05d5\u05e9\u05e8\u05d4 \u2014 \u05de\u05d8\u05e4\u05dc\u05d9\u05dd \u05e2\u05db\u05e9\u05d9\u05d5", "\u2705 \u05d1\u05d8\u05d9\u05e4\u05d5\u05dc"),
    "complete_bug":     ("\u2705 \u05d4\u05ea\u05e7\u05dc\u05d4 \u05e1\u05d5\u05de\u05e0\u05d4 \u05db\u05d4\u05d5\u05e9\u05dc\u05de\u05d4!", "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd"),
    "run_fix":          ("\u1f680 \u05ea\u05d9\u05e7\u05d5\u05df \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9 \u05d4\u05d5\u05e4\u05e2\u05dc!", "\u1f680 \u05de\u05e8\u05d9\u05e5"),
    "status_bug":       ("\u1f50d \u05d1\u05d5\u05d3\u05e7 \u05e1\u05d8\u05d8\u05d5\u05e1...", "\u1f50d"),
    "improve_bug":      ("\u2728 \u05e9\u05d5\u05dc\u05d7 \u05dc-Lovable \u05dc\u05e9\u05d9\u05e4\u05d5\u05e8", "\u2728"),
    "approve_request":  ("\u2705 \u05d4\u05d1\u05e7\u05e9\u05d4 \u05d0\u05d5\u05e9\u05e8\u05d4!", "\u2705 \u05d0\u05d5\u05e9\u05e8"),
    "reject_request":   ("\u274c \u05d4\u05d1\u05e7\u05e9\u05d4 \u05e0\u05d3\u05d7\u05ea\u05d4", "\u274c \u05e0\u05d3\u05d7\u05d4"),
    "improve_request":  ("\u2728 \u05e9\u05d5\u05dc\u05d7 \u05dc-Lovable \u05dc\u05e9\u05d9\u05e4\u05d5\u05e8", "\u2728"),
    "complete_match":   ("\u2705 \u05d4\u05d1\u05e7\u05e9\u05d4 \u05d8\u05d5\u05e4\u05dc\u05d4 \u05d1\u05d4\u05e6\u05dc\u05d7\u05d4! \u1f389", "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd"),
    "status_match":     ("\u1f50d \u05d1\u05d5\u05d3\u05e7 \u05e1\u05d8\u05d8\u05d5\u05e1...", "\u1f50d"),
    "approve_health":   ("\u2705 \u05d4\u05d3\u05d9\u05d5\u05d5\u05d7 \u05d4\u05ea\u05e7\u05d1\u05dc \u2014 \u05de\u05d8\u05e4\u05dc\u05d9\u05dd", "\u2705"),
    "complete_health":  ("\u2705 \u05d4\u05ea\u05e7\u05dc\u05d4 \u05ea\u05d5\u05e7\u05e0\u05d4!", "\u2705 \u05d4\u05d5\u05e9\u05dc\u05dd"),
    "status_health":    ("\u1f50d \u05d1\u05d5\u05d3\u05e7 \u05e1\u05d8\u05d8\u05d5\u05e1...", "\u1f50d"),
}


def handle_webhook(bot_key, formatter):
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "Empty payload"}), 400
        text, kb = formatter(data)
        token = BOTS[bot_key]["token"]
        ok = tg(token, CHAT_ID, text, kb)
        return jsonify({"status": "ok" if ok else "error"}), 200 if ok else 500
    except Exception as e:
        logging.error(f"[{bot_key}] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/webhook/leads",       methods=["POST"])
def leads():         return handle_webhook("leads",       fmt_lead)

@app.route("/webhook/bugs",        methods=["POST"])
def bugs():          return handle_webhook("bugs",        fmt_bug)

@app.route("/webhook/lovable",     methods=["POST"])
def lovable():       return handle_webhook("lovable",     fmt_lovable)

@app.route("/webhook/matchmaking", methods=["POST"])
def matchmaking():   return handle_webhook("matchmaking", fmt_matchmaking)

@app.route("/webhook/health",      methods=["POST"])
def health_report(): return handle_webhook("health",      fmt_health)


@app.route("/webhook/callback/<bot_key>", methods=["POST"])
def callback(bot_key):
    try:
        upd     = request.get_json()
        cb      = upd.get("callback_query", {})
        cb_id   = cb.get("id")
        cb_data = cb.get("data", "")
        token   = BOTS.get(bot_key, {}).get("token")
        if not token or not cb_data:
            return jsonify({"ok": True}), 200
        action  = cb_data.split(":")[0]
        rec_id  = cb_data.split(":")[1] if ":" in cb_data else ""
        long_msg, short_msg = CALLBACK_RESPONSES.get(action, ("\u2705 \u05d1\u05d5\u05e6\u05e2", "\u2705"))
        msg = f"{long_msg}\n\u1f194 \u05de\u05d6\u05d4\u05d4: {rec_id}" if rec_id else long_msg
        tg(token, CHAT_ID, msg)
        answer_callback(token, cb_id, short_msg)
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": True}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "bots": list(BOTS.keys()), "version": "3.1"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Klik Multi-Bot Agent v3.1 עולה על פורט {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
