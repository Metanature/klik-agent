#!/usr/bin/env python3
"""klik_lovable_bot v2.1 - Python 3.11 compatible, no f-string backslash"""
from flask import Flask, request, jsonify
import requests, logging, os, time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BOT_TOKEN   = "8690987639:AAH83slPs_j_H7pGSfpeGWTWirCsiJHi7Ks"
CHAT_ID     = 326460077
LOVABLE_URL = "https://lovable.dev/projects/a6749f8e-90a0-4d01-a509-5bd0d173f325"
BASE_URL    = "https://api.telegram.org/bot" + BOT_TOKEN

# Hebrew constants - defined OUTSIDE f-strings (Python 3.11 compatible)
NA   = "\u05dc\u05d0 \u05e6\u05d5\u05d9\u05df"
HIGH = "\u05d2\u05d1\u05d5\u05d4\u05d4"
MED  = "\u05d1\u05d9\u05e0\u05d5\u05e0\u05d9\u05ea"
LOW  = "\u05e0\u05de\u05d5\u05db\u05d4"

request_store = {}


def tg_send(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    r = requests.post(BASE_URL + "/sendMessage", json=payload, timeout=10)
    res = r.json()
    logging.info("[tg_send] ok=" + str(res.get("ok")))
    return res


def tg_edit(chat_id, message_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "message_id": message_id,
               "text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    r = requests.post(BASE_URL + "/editMessageText", json=payload, timeout=10)
    res = r.json()
    logging.info("[tg_edit] ok=" + str(res.get("ok")) + " msg=" + str(message_id))
    return res


def tg_answer(callback_id, text="OK", show_alert=False):
    requests.post(BASE_URL + "/answerCallbackQuery",
                  json={"callback_query_id": callback_id,
                        "text": text, "show_alert": show_alert}, timeout=5)


def main_keyboard(rid):
    return [
        [{"text": "\u2705 \u05d0\u05e9\u05e8", "callback_data": "approve:" + rid},
         {"text": "\u274c \u05d3\u05d7\u05d4", "callback_data": "reject:"  + rid}],
        [{"text": "\u2728 \u05e9\u05e4\u05e8 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8",
          "callback_data": "improve_prompt:" + rid},
         {"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1",
          "callback_data": "status:" + rid}],
        [{"text": "\ud83d\ude80 \u05e9\u05dc\u05d7 \u05dc-Lovable",
          "callback_data": "send_to_lovable:" + rid},
         {"text": "\ud83d\udd17 \u05e4\u05ea\u05d7 Lovable", "url": LOVABLE_URL}],
    ]


def build_improved_prompt(data):
    feature  = data.get("feature")      or NA
    priority = data.get("priority")     or NA
    req_by   = data.get("requested_by") or NA
    details  = data.get("details")      or NA
    pri_map  = {HIGH: "\ud83d\udd34", MED: "\ud83d\udfe1", LOW: "\ud83d\udfe2"}
    pe       = pri_map.get(priority, "\ud83d\udfe3")
    return "\n".join([
        "\u2728 <b>\u05e4\u05e8\u05d5\u05de\u05e4\u05d8 \u05de\u05e9\u05d5\u05e4\u05e8 \u05dc-Lovable</b>",
        "",
        "<b>1. \u05de\u05d8\u05e8\u05d4:</b> " + feature,
        "",
        "<b>2. \u05d1\u05e2\u05d9\u05d4:</b> " + details,
        "",
        "<b>3. \u05de\u05d4 \u05e6\u05e8\u05d9\u05da \u05dc\u05e9\u05e0\u05d5\u05ea:</b>",
        "\u2022 UI \u05d0\u05dd \u05e0\u05d3\u05e8\u05e9",
        "\u2022 \u05dc\u05d5\u05d2\u05d9\u05e7\u05d4 \u05e2\u05e1\u05e7\u05d9\u05ea",
        "\u2022 State \u05d0\u05dd \u05e8\u05dc\u05d5\u05d5\u05e0\u05d8\u05d9",
        "",
        "<b>4. \u05d3\u05e8\u05d9\u05e9\u05d5\u05ea:</b>",
        "\u2022 " + feature,
        "\u2022 " + pe + " " + priority,
        "\u2022 \u05de\u05d1\u05e7\u05e9: " + req_by,
        "\u2022 " + details,
        "",
        "<b>5. \u05de\u05d2\u05d1\u05dc\u05d5\u05ea:</b>",
        "\u2022 \u05d0\u05dc \u05ea\u05e9\u05e0\u05d4 \u05e7\u05d5\u05d3 \u05e9\u05dc\u05d0 \u05e7\u05e9\u05d5\u05e8",
        "\u2022 \u05d0\u05dc \u05ea\u05e9\u05d1\u05d5\u05e8 \u05e4\u05d9\u05e6\u05e8\u05d9\u05dd \u05e7\u05d9\u05d9\u05de\u05d9\u05dd",
        "",
        "<b>6. \u05ea\u05d5\u05e6\u05d0\u05d4:</b>",
        "\u05d4\u05e4\u05d9\u05e6\u05e8 \"" + feature + "\" \u05e2\u05d5\u05d1\u05d3 \u05d1\u05de\u05dc\u05d5\u05d0\u05d5.",
    ])


@app.route("/webhook/lovable", methods=["POST"])
def lovable_webhook():
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        if not data:
            return jsonify({"status": "error", "message": "Empty"}), 400
        rid = data.get("id") or ("req_" + str(len(request_store) + 1))
        now = time.time()
        request_store[rid] = {"data": data, "improved_prompt": None,
                               "status": "created", "created_at": now, "updated_at": now}
        feature  = data.get("feature")      or NA
        priority = data.get("priority")     or NA
        req_by   = data.get("requested_by") or NA
        details  = data.get("details")      or NA
        pri_map  = {HIGH: "\ud83d\udd34", MED: "\ud83d\udfe1", LOW: "\ud83d\udfe2"}
        pe       = pri_map.get(priority, "\ud83d\udfe3")
        text = ("\ud83d\udfe3 <b>\u05d1\u05e7\u05e9\u05d4 \u05d7\u05d3\u05e9\u05d4 \u05d1-Lovable!</b>\n"
                + "\ud83e\ude84 " + feature + "\n"
                + pe + " " + priority + "\n"
                + "\ud83d\udc64 " + req_by + "\n"
                + "\ud83d\udcdd " + details + "\n"
                + "\ud83d\udd11 ID: " + rid)
        result = tg_send(CHAT_ID, text, main_keyboard(rid))
        logging.info("[lovable] rid=" + rid + " tg_ok=" + str(result.get("ok")))
        return jsonify({"status": "ok", "request_id": rid,
                        "telegram_ok": result.get("ok")}), 200
    except Exception as e:
        logging.error("[lovable] " + str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


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
        logging.info("[cb] id=" + cb_id + " data=" + cb_data)
        if not cb_data or ":" not in cb_data:
            tg_answer(cb_id, "no data")
            return jsonify({"ok": True}), 200
        action, rid = cb_data.split(":", 1)
        store = request_store.get(rid)
        now   = time.time()

        if action == "improve_prompt":
            if not store:
                tg_answer(cb_id, "Not found")
                return jsonify({"ok": True, "handler": "improve_prompt", "result": "FAIL_no_rid"}), 200
            tg_answer(cb_id, "Building prompt...")
            improved = build_improved_prompt(store["data"])
            store["improved_prompt"] = improved
            store["status"] = "improved"
            store["updated_at"] = now
            result = tg_edit(chat_id, msg_id, improved, keyboard=[
                [{"text": "\ud83d\ude80 \u05e9\u05dc\u05d7 \u05dc-Lovable",
                  "callback_data": "send_to_lovable:" + rid},
                 {"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1",
                  "callback_data": "status:" + rid}],
                [{"text": "\ud83d\udd17 Lovable", "url": LOVABLE_URL}],
            ])
            logging.info("[cb] HANDLER=improve_prompt rid=" + rid + " ok=" + str(result.get("ok")))
            return jsonify({"ok": True, "handler": "improve_prompt", "rid": rid,
                           "edit_ok": result.get("ok"),
                           "result": "PASS" if result.get("ok") else "FAIL"}), 200

        elif action == "send_to_lovable":
            if not store:
                tg_answer(cb_id, "Not found")
                return jsonify({"ok": True, "handler": "send_to_lovable", "result": "FAIL_no_rid"}), 200
            tg_answer(cb_id, "Sending...")
            prompt  = store.get("improved_prompt") or build_improved_prompt(store["data"])
            feature = store["data"].get("feature") or NA
            msg = ("\ud83d\ude80 <b>\u05e9\u05dc\u05d9\u05d7\u05d4 \u05dc-Lovable</b>\n"
                   + "\ud83d\udd11 ID: " + rid + "\n"
                   + "\ud83e\ude84 " + feature + "\n\n"
                   + prompt)
            store["status"] = "sent"
            store["updated_at"] = now
            result = tg_send(chat_id, msg, keyboard=[
                [{"text": "\ud83d\udd17 Lovable", "url": LOVABLE_URL}],
                [{"text": "\ud83d\udcca \u05e1\u05d8\u05d8\u05d5\u05e1",
                  "callback_data": "status:" + rid}],
            ])
            logging.info("[cb] HANDLER=send_to_lovable rid=" + rid + " ok=" + str(result.get("ok")))
            return jsonify({"ok": True, "handler": "send_to_lovable", "rid": rid,
                           "send_ok": result.get("ok"),
                           "result": "PASS" if result.get("ok") else "FAIL"}), 200

        elif action == "status":
            if not store:
                tg_answer(cb_id, "Not found")
                return jsonify({"ok": True, "handler": "status", "result": "FAIL_no_rid"}), 200
            tg_answer(cb_id, "Loading...")
            feature = store["data"].get("feature") or NA
            status  = store.get("status", "unknown")
            has_p   = "\u2705 \u05db\u05df" if store.get("improved_prompt") else "\u274c \u05d8\u05e8\u05dd"
            msg = ("\ud83d\udcca <b>\u05e1\u05d8\u05d8\u05d5\u05e1</b>\n"
                   + "\ud83d\udd11 ID: " + rid + "\n"
                   + "\ud83e\ude84 " + feature + "\n"
                   + "\ud83d\udccc \u05de\u05e6\u05d1: " + status + "\n"
                   + "\u2728 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8: " + has_p)
            result = tg_send(chat_id, msg, keyboard=[
                [{"text": "\u2728 \u05e9\u05e4\u05e8 \u05e4\u05e8\u05d5\u05de\u05e4\u05d8",
                  "callback_data": "improve_prompt:" + rid}],
                [{"text": "\ud83d\ude80 \u05e9\u05dc\u05d7 \u05dc-Lovable",
                  "callback_data": "send_to_lovable:" + rid}],
            ])
            logging.info("[cb] HANDLER=status rid=" + rid + " ok=" + str(result.get("ok")))
            return jsonify({"ok": True, "handler": "status", "rid": rid,
                           "status": status,
                           "result": "PASS" if result.get("ok") else "FAIL"}), 200

        elif action == "approve":
            tg_answer(cb_id, "Approved!")
            if store:
                store["status"] = "approved"; store["updated_at"] = now
            tg_send(chat_id, "\u2705 \u05d1\u05e7\u05e9\u05d4 " + rid + " \u05d0\u05d5\u05e9\u05e8\u05d4!")
            return jsonify({"ok": True, "handler": "approve", "rid": rid}), 200

        elif action == "reject":
            tg_answer(cb_id, "Rejected")
            if store:
                store["status"] = "rejected"; store["updated_at"] = now
            tg_send(chat_id, "\u274c \u05d1\u05e7\u05e9\u05d4 " + rid + " \u05e0\u05d3\u05d7\u05ea\u05d4.")
            return jsonify({"ok": True, "handler": "reject", "rid": rid}), 200

        else:
            tg_answer(cb_id, "Unknown: " + action)
            return jsonify({"ok": True, "handler": "unknown", "action": action}), 200

    except Exception as e:
        logging.error("[cb] EXCEPTION: " + str(e))
        return jsonify({"ok": True, "error": str(e)}), 200


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "bot": "klik_lovable_bot",
                    "version": "2.1", "requests_stored": len(request_store)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("klik_lovable_bot v2.1 - port " + str(port))
    app.run(host="0.0.0.0", port=port, debug=False)
