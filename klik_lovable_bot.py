#!/usr/bin/env python3
"""
klik_lovable_bot.py v2.0
Bot: @klik_lovable_bot
Buttons: improve_prompt | send_to_lovable | status
"""
from flask import Flask, request, jsonify
import requests, logging, os, time

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

BOT_TOKEN   = "8690987639:AAH83slPs_j_H7pGSfpeGWTWirCsiJHi7Ks"
CHAT_ID     = 326460077
LOVABLE_URL = "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325"
BASE_URL    = f"https://api.telegram.org/bot{BOT_TOKEN}"

# â”€â”€â”€ In-memory store â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# rid â†’ {
#   "data":           original payload,
#   "improved_prompt": str or None,
#   "status":         "created" | "improved" | "sent",
#   "created_at":     float,
#   "updated_at":     float,
# }
request_store: dict = {}


# â”€â”€â”€ Telegram helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def tg_send(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    result = r.json()
    logging.info(f"[tg_send] ok={result.get('ok')} chat={chat_id}")
    return result


def tg_edit(chat_id, message_id, text, keyboard=None):
    payload = {
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       text,
        "parse_mode": "HTML",
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    r = requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)
    result = r.json()
    logging.info(f"[tg_edit] ok={result.get('ok')} msg={message_id}")
    return result


def tg_answer(callback_id, text="âœ…", show_alert=False):
    requests.post(
        f"{BASE_URL}/answerCallbackQuery",
        json={"callback_query_id": callback_id, "text": text, "show_alert": show_alert},
        timeout=5,
    )


def main_keyboard(rid):
    """Standard keyboard attached to every request message."""
    return [
        [
            {"text": "âœ… ××©×¨",  "callback_data": f"approve:{rid}"},
            {"text": "âŒ ×“×—×”",  "callback_data": f"reject:{rid}"},
        ],
        [
            {"text": "âœ¨ ×©×¤×¨ ×¤×¨×•×ž×¤×˜", "callback_data": f"improve_prompt:{rid}"},
            {"text": "ðŸ“Š ×¡×˜×˜×•×¡",      "callback_data": f"status:{rid}"},
        ],
        [
            {"text": "ðŸš€ ×©×œ×— ×œ-Lovable", "callback_data": f"send_to_lovable:{rid}"},
            {"text": "ðŸ”— ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL},
        ],
    ]


# â”€â”€â”€ Prompt builders â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_improved_prompt(data: dict) -> str:
    feature      = data.get("feature",      "×œ× ×¦×•×™×Ÿ")
    priority     = data.get("priority",     "×œ× ×¦×•×™×Ÿ")
    requested_by = data.get("requested_by", "×œ× ×¦×•×™×Ÿ")
    details      = data.get("details",      "×œ× ×¦×•×™×Ÿ")
    pe = {"×’×‘×•×”×”": "ðŸ”´", "×‘×™× ×•× ×™×ª": "ðŸŸ¡", "× ×ž×•×›×”": "ðŸŸ¢"}.get(priority, "ðŸŸ£")

    return (
        f"âœ¨ <b>×¤×¨×•×ž×¤×˜ ×ž×©×•×¤×¨ ×œ-Lovable</b>\n\n"
        f"<b>1ï¸âƒ£ ×ž×˜×¨×”:</b>\n"
        f"×œ×ž×ž×© ××ª ×”×¤×™×¦'×¨: <b>{feature}</b>\n\n"
        f"<b>2ï¸âƒ£ ×ž×” ×”×‘×¢×™×”:</b>\n"
        f"{details}\n\n"
        f"<b>3ï¸âƒ£ ×ž×” ×¦×¨×™×š ×œ×©× ×•×ª:</b>\n"
        f"â€¢ ×¢×“×›×•×Ÿ ×ž×ž×©×§ ×ž×©×ª×ž×© ×× × ×“×¨×©\n"
        f"â€¢ ×¢×“×›×•×Ÿ ×œ×•×’×™×§×” ×¢×¡×§×™×ª ×‘×œ×‘×“ ×œ×¤×™×¦'×¨ ×–×”\n"
        f"â€¢ ×¢×“×›×•×Ÿ state management ×× ×¨×œ×•×•× ×˜×™\n\n"
        f"<b>4ï¸âƒ£ ×“×¨×™×©×•×ª ×ž×“×•×™×§×•×ª:</b>\n"
        f"â€¢ ×¤×™×¦'×¨: {feature}\n"
        f"â€¢ ×¢×“×™×¤×•×ª: {pe} {priority}\n"
        f"â€¢ ×ž×‘×•×§×© ×¢\"×™: {requested_by}\n"
        f"â€¢ ×¤×¨×˜×™×: {details}\n\n"
        f"<b>5ï¸âƒ£ ×ž×’×‘×œ×•×ª:</b>\n"
        f"â€¢ ××œ ×ª×©× ×” ×§×•×“ ×©××™× ×• ×§×©×•×¨ ×œ×¤×™×¦'×¨ ×–×”\n"
        f"â€¢ ××œ ×ª×©×‘×•×¨ ×¤×™×¦'×¨×™× ×§×™×™×ž×™×\n"
        f"â€¢ ××œ ×ª×•×¡×™×£ ×—×‘×™×œ×•×ª ×œ×œ× ××™×©×•×¨\n\n"
        f"<b>6ï¸âƒ£ ×ª×•×¦××” ×¨×¦×•×™×”:</b>\n"
        f"×”×¤×™×¦'×¨ \"{feature}\" ×¢×•×‘×“ ×‘×ž×œ×•××• ×•×œ× ×©×•×‘×¨ ×“×‘×¨ ×§×™×™×."
    )


def build_send_message(rid: str, store: dict) -> str:
    data     = store.get("data", {})
    prompt   = store.get("improved_prompt") or build_improved_prompt(data)
    feature  = data.get("feature", "×œ× ×¦×•×™×Ÿ")
    ts       = time.strftime("%H:%M:%S", time.localtime(store.get("updated_at", time.time())))

    return (
        f"ðŸš€ <b>×©×œ×™×—×” ×œ-Lovable</b>\n"
        f"ðŸ“‹ request_id: <code>{rid}</code>\n"
        f"ðŸª„ ×¤×™×¦'×¨: {feature}\n"
        f"ðŸ• ×¢×•×“×›×Ÿ: {ts}\n\n"
        f"ðŸ“ <b>×¤×¨×•×ž×¤×˜ ×œ×”×“×‘×§×”:</b>\n"
        f"<pre>{prompt}</pre>\n\n"
        f"ðŸ‘† ×”×¢×ª×§ ××ª ×”×¤×¨×•×ž×¤×˜ ×•×”×“×‘×§ ×™×©×™×¨×•×ª ×‘-Lovable"
    )


def build_status_message(rid: str, store: dict) -> str:
    data     = store.get("data", {})
    status   = store.get("status", "unknown")
    feature  = data.get("feature",  "×œ× ×¦×•×™×Ÿ")
    priority = data.get("priority", "×œ× ×¦×•×™×Ÿ")
    created  = time.strftime("%H:%M:%S", time.localtime(store.get("created_at", 0)))
    updated  = time.strftime("%H:%M:%S", time.localtime(store.get("updated_at", 0)))

    status_map = {
        "created":  "ðŸŸ¡ × ×•×¦×¨ â€” ×ž×ž×ª×™×Ÿ ×œ×˜×™×¤×•×œ",
        "improved": "ðŸ”µ ×¤×¨×•×ž×¤×˜ ×©×•×¤×¨ â€” ×ž×•×›×Ÿ ×œ×©×œ×™×—×”",
        "sent":     "ðŸŸ¢ × ×©×œ×— ×œ-Lovable",
        "approved": "âœ… ××•×©×¨",
        "rejected": "âŒ × ×“×—×”",
    }
    status_text = status_map.get(status, f"âšª {status}")
    has_prompt  = "âœ… ×›×Ÿ" if store.get("improved_prompt") else "âŒ ×˜×¨× ×©×•×¤×¨"

    return (
        f"ðŸ“Š <b>×¡×˜×˜×•×¡ ×‘×§×©×”</b>\n\n"
        f"ðŸ”‘ request_id: <code>{rid}</code>\n"
        f"ðŸª„ ×¤×™×¦'×¨: {feature}\n"
        f"ðŸŸ£ ×¢×“×™×¤×•×ª: {priority}\n\n"
        f"<b>×ž×¦×‘ × ×•×›×—×™:</b> {status_text}\n"
        f"<b>×¤×¨×•×ž×¤×˜ ×ž×©×•×¤×¨:</b> {has_prompt}\n\n"
        f"ðŸ• × ×•×¦×¨: {created}\n"
        f"ðŸ•‘ ×¢×•×“×›×Ÿ: {updated}"
    )


# â”€â”€â”€ Incoming webhook: new Lovable request â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route("/webhook/lovable", methods=["POST"])
def lovable_webhook():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "Empty payload"}), 400

        rid = data.get("id") or f"req_{len(request_store) + 1}"
        now = time.time()
        request_store[rid] = {
            "data":            data,
            "improved_prompt": None,
            "status":          "created",
            "created_at":      now,
            "updated_at":      now,
        }
        logging.info(f"[lovable] Stored rid={rid} feature={data.get('feature')}")

        feature  = data.get("feature",      "×œ× ×¦×•×™×Ÿ")
        priority = data.get("priority",     "×œ× ×¦×•×™×Ÿ")
        req_by   = data.get("requested_by", "×œ× ×¦×•×™×Ÿ")
        details  = data.get("details",      "×œ× ×¦×•×™×Ÿ")
        pe       = {"×’×‘×•×”×”": "ðŸ”´", "×‘×™× ×•× ×™×ª": "ðŸŸ¡", "× ×ž×•×›×”": "ðŸŸ¢"}.get(priority, "ðŸŸ£")

        text = (
            f"ðŸŸ£ <b>×‘×§×©×” ×—×“×©×” ×‘-Lovable!</b>\n"
            f"ðŸª„ ×¤×™×¦'×¨: {feature}\n"
            f"{pe} ×¢×“×™×¤×•×ª: {priority}\n"
            f"ðŸ‘¤ ×ž×‘×§×©: {req_by}\n"
            f"ðŸ“ ×¤×¨×˜×™×: {details}\n"
            f"ðŸ”‘ ID: <code>{rid}</code>"
        )

        result = tg_send(CHAT_ID, text, main_keyboard(rid))
        return jsonify({
            "status":      "ok",
            "request_id":  rid,
            "telegram_ok": result.get("ok"),
        }), 200

    except Exception as e:
        logging.error(f"[lovable] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# â”€â”€â”€ Telegram callback handler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route("/webhook/callback", methods=["POST"])
def callback():
    try:
        upd     = request.get_json()
        cb      = upd.get("callback_query", {})
        cb_id   = cb.get("id", "")
        cb_data = cb.get("data", "")
        message = cb.get("message", {})
        msg_id  = message.get("message_id")
        chat_id = message.get("chat", {}).get("id", CHAT_ID)

        logging.info(f"[callback] callback_query_id={cb_id} data={cb_data} endpoint=/webhook/callback")

        if not cb_data:
            tg_answer(cb_id, "âš ï¸ ××™×Ÿ × ×ª×•× ×™×")
            return jsonify({"ok": True}), 200

        if ":" not in cb_data:
            tg_answer(cb_id, "âš ï¸ ×¤×•×¨×ž×˜ ×œ× ×ª×§×™×Ÿ")
            return jsonify({"ok": True}), 200

        action, rid = cb_data.split(":", 1)
        store       = request_store.get(rid)
        now         = time.time()

        logging.info(f"[callback] action={action} rid={rid} found={'yes' if store else 'NO'}")

        # â”€â”€ HANDLER: improve_prompt â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if action == "improve_prompt":
            if not store:
                tg_answer(cb_id, "âŒ ×‘×§×©×” ×œ× × ×ž×¦××”", show_alert=True)
                logging.warning(f"[improve_prompt] rid={rid} NOT in store")
                return jsonify({"ok": True, "handler": "improve_prompt", "result": "FAIL_no_rid"}), 200

            tg_answer(cb_id, "â³ ×ž×™×™×¦×¨ ×¤×¨×•×ž×¤×˜ ×ž×©×•×¤×¨...")

            improved = build_improved_prompt(store["data"])
            store["improved_prompt"] = improved
            store["status"]          = "improved"
            store["updated_at"]      = now

            result = tg_edit(chat_id, msg_id, improved, keyboard=[
                [
                    {"text": "ðŸš€ ×©×œ×— ×œ-Lovable", "callback_data": f"send_to_lovable:{rid}"},
                    {"text": "ðŸ“Š ×¡×˜×˜×•×¡",          "callback_data": f"status:{rid}"},
                ],
                [{"text": "ðŸ”— ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL}],
            ])

            logging.info(
                f"[callback] HANDLER=improve_prompt | rid={rid} | "
                f"callback_query_id={cb_id} | edit_ok={result.get('ok')} | RESULT=PASS"
            )
            return jsonify({
                "ok":      True,
                "handler": "improve_prompt",
                "rid":     rid,
                "edit_ok": result.get("ok"),
                "result":  "PASS" if result.get("ok") else "FAIL_tg_edit",
            }), 200

        # â”€â”€ HANDLER: send_to_lovable â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        elif action == "send_to_lovable":
            if not store:
                tg_answer(cb_id, "âŒ ×‘×§×©×” ×œ× × ×ž×¦××”", show_alert=True)
                logging.warning(f"[send_to_lovable] rid={rid} NOT in store")
                return jsonify({"ok": True, "handler": "send_to_lovable", "result": "FAIL_no_rid"}), 200

            tg_answer(cb_id, "ðŸš€ ×©×•×œ×— ×œ-Lovable...")

            msg_text = build_send_message(rid, store)
            store["status"]     = "sent"
            store["updated_at"] = now

            result = tg_send(chat_id, msg_text, keyboard=[
                [{"text": "ðŸ”— ×¤×ª×— ×‘-Lovable", "url": LOVABLE_URL}],
                [{"text": "ðŸ“Š ×¡×˜×˜×•×¡", "callback_data": f"status:{rid}"}],
            ])

            logging.info(
                f"[callback] HANDLER=send_to_lovable | rid={rid} | "
                f"callback_query_id={cb_id} | send_ok={result.get('ok')} | RESULT=PASS"
            )
            return jsonify({
                "ok":      True,
                "handler": "send_to_lovable",
                "rid":     rid,
                "send_ok": result.get("ok"),
                "result":  "PASS" if result.get("ok") else "FAIL_tg_send",
            }), 200

        # â”€â”€ HANDLER: status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        elif action == "status":
            if not store:
                tg_answer(cb_id, "âŒ ×‘×§×©×” ×œ× × ×ž×¦××”", show_alert=True)
                logging.warning(f"[status] rid={rid} NOT in store")
                return jsonify({"ok": True, "handler": "status", "result": "FAIL_no_rid"}), 200

            tg_answer(cb_id, "ðŸ“Š ×˜×•×¢×Ÿ ×¡×˜×˜×•×¡...")

            msg_text = build_status_message(rid, store)
            result   = tg_send(chat_id, msg_text, keyboard=[
                [{"text": "âœ¨ ×©×¤×¨ ×¤×¨×•×ž×¤×˜",   "callback_data": f"improve_prompt:{rid}"}],
                [{"text": "ðŸš€ ×©×œ×— ×œ-Lovable","callback_data": f"send_to_lovable:{rid}"}],
            ])

            logging.info(
                f"[callback] HANDLER=status | rid={rid} | "
                f"callback_query_id={cb_id} | send_ok={result.get('ok')} | RESULT=PASS"
            )
            return jsonify({
                "ok":      True,
                "handler": "status",
                "rid":     rid,
                "send_ok": result.get("ok"),
                "status":  store.get("status"),
                "result":  "PASS" if result.get("ok") else "FAIL_tg_send",
            }), 200

        # â”€â”€ HANDLER: approve â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        elif action == "approve":
            tg_answer(cb_id, "âœ… ××•×©×¨!")
            if store:
                store["status"]     = "approved"
                store["updated_at"] = now
            result = tg_send(chat_id, f"âœ… ×”×‘×§×©×” <code>{rid}</code> <b>××•×©×¨×”!</b>")
            logging.info(f"[callback] HANDLER=approve | rid={rid} | send_ok={result.get('ok')}")
            return jsonify({"ok": True, "handler": "approve", "rid": rid}), 200

        # â”€â”€ HANDLER: reject â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        elif action == "reject":
            tg_answer(cb_id, "âŒ × ×“×—×”")
            if store:
                store["status"]     = "rejected"
                store["updated_at"] = now
            result = tg_send(chat_id, f"âŒ ×”×‘×§×©×” <code>{rid}</code> <b>× ×“×—×ª×”.</b>")
            logging.info(f"[callback] HANDLER=reject | rid={rid} | send_ok={result.get('ok')}")
            return jsonify({"ok": True, "handler": "reject", "rid": rid}), 200

        # â”€â”€ UNKNOWN ACTION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        else:
            tg_answer(cb_id, f"âš ï¸ ×¤×¢×•×œ×” ×œ× ×ž×•×›×¨×ª: {action}")
            logging.warning(f"[callback] UNKNOWN action={action} rid={rid}")
            return jsonify({"ok": True, "handler": "unknown", "action": action}), 200

    except Exception as e:
        logging.error(f"[callback] EXCEPTION: {e}")
        return jsonify({"ok": True, "error": str(e)}), 200


# â”€â”€â”€ Health check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status":          "ok",
        "bot":             "klik_lovable_bot",
        "version":         "2.0",
        "requests_stored": len(request_store),
    }), 200


# â”€â”€â”€ Entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"ðŸš€ klik_lovable_bot v2.0 â€” port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
