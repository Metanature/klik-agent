#!/usr/bin/env python3
"""
Klik Multi-Bot Agent v3 â€” 5 Bots + Inline Keyboards + Callback Handling
"""
from flask import Flask, request, jsonify
import requests, json, logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CHAT_ID = 326460077
BOTS = {
    "leads":       {"token": "8643090938:AAGo55jGaZFlzKJm63_QPcpQPp2Ow5p5vFw", "name": "×œ×™×“×™× × ×›× ×¡×™×"},
    "bugs":        {"token": "8785442399:AAFTsUKKe55l31yjfeAs_-g2TRxYqtvWdp8", "name": "×ª×§×œ×•×ª ×˜×›× ×™×•×ª"},
    "lovable":     {"token": "8690987639:AAH83slPs_j_H7pGSfpeGWTWirCsiJHi7Ks", "name": "×‘×§×©×•×ª Lovable"},
    "matchmaking": {"token": "8622414362:AAFYG8Qk_5oQYTmOdxx6CccMaDhh2fpTZmk", "name": "×”×¦×¢×•×ª ×œ×©×™×“×•×¨×’×™×"},
    "health":      {"token": "8706328171:AAHGB5bLM1oe4ZdqkPR4AEk4ld_kp6jhMe8", "name": "×“×™×•×•×— ×¢×œ ×ª×§×œ×”"},
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


def answer_callback(token, callback_id, text="âœ…"):
    requests.post(f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                  json={"callback_query_id": callback_id, "text": text}, timeout=5)


def fmt_lead(d):
    lid   = d.get("id", "")
    phone = clean_phone(d.get("phone", "0500000000"))
    text = (
        "ðŸ”¥ <b>×œ×§×•×— ×—×“×©!</b>\n"
        f"ðŸ‘¤ ×©×: {d.get('name','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ”§ ×©×™×¨×•×ª: {d.get('service','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ž×™×§×•×: {d.get('location','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ž ×˜×œ×¤×•×Ÿ: {d.get('phone','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ª×™××•×¨: {d.get('description','×œ× ×¦×•×™×Ÿ')}"
    )
    kb = [
        [
            {"text": "ðŸ“ž ×”×ª×§×©×¨ ×¢×›×©×™×•", "url": f"https://wa.me/{phone}?text=×©×œ×•×"},
            {"text": "ðŸ’¬ WhatsApp",     "url": f"https://wa.me/{phone}"},
        ],
        [
            {"text": "âŒ ×¡×’×•×¨ ×œ×™×“",   "callback_data": f"close_lead:{lid}"},
            {"text": "â° ×ª×–×›×•×¨×ª 2×©", "callback_data": f"snooze_lead:{lid}"},
        ],
    ]
    return text, kb


def fmt_bug(d):
    bid = d.get("id", "")
    sev = {"×’×‘×•×”×”": "ðŸ”´", "×‘×™× ×•× ×™×ª": "ðŸŸ¡", "× ×ž×•×›×”": "ðŸŸ¢"}.get(d.get("severity",""), "ðŸ”´")
    text = (
        "ðŸ”´ <b>×ª×§×œ×” ×—×“×©×”!</b>\n"
        f"ðŸ“Œ × ×•×©×: {d.get('title','×œ× ×¦×•×™×Ÿ')}\n"
        f"{sev} ×—×•×ž×¨×”: {d.get('severity','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ‘¤ ×ž×“×•×•×—: {d.get('reported_by','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ª×™××•×¨: {d.get('description','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ”— ×§×™×©×•×¨: {d.get('url','×œ× ×¦×•×™×Ÿ')}"
    )
    kb = [
        [
            {"text": "âœ… ××©×¨ ×•×ª×§×Ÿ",      "callback_data": f"approve_bug:{bid}"},
            {"text": "âœ… ×”×•×©×œ×",          "callback_data": f"complete_bug:{bid}"},
        ],
        [
            {"text": "ðŸ”“ ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL},
            {"text": "ðŸš€ ×”×¨×¥ ×¢×›×©×™×•",     "callback_data": f"run_fix:{bid}"},
        ],
        [
            {"text": "ðŸ” ×¡×˜×˜×•×¡",         "callback_data": f"status_bug:{bid}"},
            {"text": "âœ¨ ×©×¤×¨ ×¢×•×“",        "callback_data": f"improve_bug:{bid}"},
        ],
    ]
    return text, kb


def fmt_lovable(d):
    rid = d.get("id", "")
    pri = {"×’×‘×•×”×”": "ðŸ”´", "×‘×™× ×•× ×™×ª": "ðŸŸ¡", "× ×ž×•×›×”": "ðŸŸ¢"}.get(d.get("priority",""), "ðŸ”µ")
    details = d.get("details","")
    text = (
        "ðŸ”µ <b>×‘×§×©×” ×—×“×©×” ×‘-Lovable!</b>\n"
        f"ðŸª¡ ×¤×™×¦'×¨: {d.get('feature','×œ× ×¦×•×™×Ÿ')}\n"
        f"{pri} ×¢×“×™×¤×•×ª: {d.get('priority','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ‘¤ ×ž×‘×§×©: {d.get('requested_by','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×¤×¨×˜×™×: {details}"
    )
    kb = [
        [
            {"text": "âœ… ××©×¨",            "callback_data": f"approve_request:{rid}"},
            {"text": "âŒ ×“×—×”",            "callback_data": f"reject_request:{rid}"},
        ],
        [
            {"text": "ðŸš€ ×©×œ×— ×œ-Lovable", "url": LOVABLE_URL},
            {"text": "âœ¨ ×©×¤×¨ ×¢×•×“",        "callback_data": f"improve_request:{rid}"},
        ],
    ]
    return text, kb


def fmt_matchmaking(d):
    mid = d.get("id", "")
    text = (
        "ðŸŸ£ <b>×”×¦×¢×ª ×©×™×“×•×š ×—×“×©×”!</b>\n"
        f"ðŸ‘¤ ×©×: {d.get('name','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸŽ‚ ×’×™×œ: {d.get('age','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ž×™×§×•×: {d.get('location','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ž ×˜×œ×¤×•×Ÿ: {d.get('phone','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ª×™××•×¨: {d.get('description','×œ× ×¦×•×™×Ÿ')}"
    )
    kb = [
        [
            {"text": "âœ… ×”×•×©×œ×",          "callback_data": f"complete_match:{mid}"},
            {"text": "ðŸ” ×¡×˜×˜×•×¡",         "callback_data": f"status_match:{mid}"},
        ],
        [
            {"text": "ðŸ”“ ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL},
            {"text": "âœ¨ ×©×¤×¨ ×¤×¨×•×¤×™×œ",    "url": f"{LOVABLE_URL}?message=×©×¤×¨+×¤×¨×•×¤×™×œ:{d.get('name','')}"},
        ],
    ]
    return text, kb


def fmt_health(d):
    hid = d.get("id", "")
    text = (
        "ðŸ©º <b>×“×™×•×•×— ×¢×œ ×ª×§×œ×”!</b>\n"
        f"ðŸ“Œ ×›×•×ª×¨×ª: {d.get('title','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ‘¤ ×ž×“×•×•×—: {d.get('reported_by','×œ× ×¦×•×™×Ÿ')}\n"
        f"ðŸ“ ×ª×™××•×¨: {d.get('description','×œ× ×¦×•×™×Ÿ')}\n"
        f"âš ï¸ ×“×—×™×¤×•×ª: {d.get('urgency','×œ× ×¦×•×™×Ÿ')}"
    )
    kb = [
        [
            {"text": "âœ… ××™×©×¨×ª×™",         "callback_data": f"approve_health:{hid}"},
            {"text": "ðŸ”“ ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL},
        ],
        [
            {"text": "âœ… ×”×•×©×œ×",          "callback_data": f"complete_health:{hid}"},
            {"text": "ðŸ“Š ×¡×˜×˜×•×¡",         "callback_data": f"status_health:{hid}"},
        ],
    ]
    return text, kb


CALLBACK_RESPONSES = {
    "close_lead":       ("âœ… ×”×œ×™×“ × ×¡×’×¨ ×‘×”×¦×œ×—×”", "âŒ ×œ×™×“ × ×¡×’×¨"),
    "snooze_lead":      ("â° ×ª×–×›×•×¨×ª × ×§×‘×¢×” ×œ×¢×•×“ 2 ×©×¢×•×ª", "â° ×ª×–×›×•×¨×ª"),
    "approve_bug":      ("âœ… ×”×ª×§×œ×” ××•×©×¨×” â€” ×ž×˜×¤×œ×™× ×¢×›×©×™×•", "âœ… ×‘×˜×™×¤×•×œ"),
    "complete_bug":     ("âœ… ×”×ª×§×œ×” ×¡×•×ž× ×” ×›×”×•×©×œ×ž×”!", "âœ… ×”×•×©×œ×"),
    "run_fix":          ("ðŸš€ ×ª×™×§×•×Ÿ ××•×˜×•×ž×˜×™ ×”×•×¤×¢×œ!", "ðŸš€ ×ž×¨×™×¥"),
    "status_bug":       ("ðŸ” ×‘×•×“×§ ×¡×˜×˜×•×¡...", "ðŸ”"),
    "improve_bug":      ("âœ¨ ×©×•×œ×— ×œ-Lovable ×œ×©×™×¤×•×¨", "âœ¨"),
    "approve_request":  ("âœ… ×”×‘×§×©×” ××•×©×¨×”!", "âœ… ××•×©×¨"),
    "reject_request":   ("âŒ ×”×‘×§×©×” × ×“×—×ª×”", "âŒ × ×“×—×”"),
    "improve_request":  ("âœ¨ ×©×•×œ×— ×œ-Lovable ×œ×©×™×¤×•×¨", "âœ¨"),
    "complete_match":   ("âœ… ×”×‘×§×©×” ×˜×•×¤×œ×” ×‘×”×¦×œ×—×”! ðŸŽ‰", "âœ… ×”×•×©×œ×"),
    "status_match":     ("ðŸ” ×‘×•×“×§ ×¡×˜×˜×•×¡...", "ðŸ”"),
    "approve_health":   ("âœ… ×“×™×•×•×— ×”×ª×§×‘×œ â€” ×ž×˜×¤×œ×™×", "âœ…"),
    "complete_health":  ("âœ… ×”×ª×§×œ×” ×ª×•×§× ×”!", "âœ… ×”×•×©×œ×"),
    "status_health":    ("ðŸ” ×‘×•×“×§ ×¡×˜×˜×•×¡...", "ðŸ”"),
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
        long_msg, short_msg = CALLBACK_RESPONSES.get(action, ("âœ… ×‘×•×¦×¢", "âœ…"))
        msg = f"{long_msg}\nðŸ†” ×ž×–×”×”: {rec_id}" if rec_id else long_msg
        tg(token, CHAT_ID, msg)
        answer_callback(token, cb_id, short_msg)
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"ok": True}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "bots": list(BOTS.keys()), "version": "3.1"}), 200


if __name__ == "__main__":
    print("ðŸš€ Klik Multi-Bot Agent v3.1 â€” 5 Bots + Buttons")
    app.run(host="0.0.0.0", port=5000, debug=False)
