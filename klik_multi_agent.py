from flask import Flask, request, jsonify
import requests, json, logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CHAT_ID = 326460077
BOTS = {
    "leads":       {"token": "8643090938:AAHXQF-Rx_h19fuw8e9uJ2tp7z-TqUXSRtA"},
    "bugs":        {"token": "8785442399:AAEJr4_tVOw1Kq_s2-QdX0pBQ_IMtdlzs0Y"},
    "lovable":     {"token": "8690987639:AAHdtvfPjaU8S4NpHXsMTOaYu7OPEa9P7Fc"},
    "matchmaking": {"token": "8622414362:AAGTQMSxkNLSbYPPvbQWKpmlJAupXRIf_Ac"},
}

def send_telegram(token, message):
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": message}, timeout=10)

def fmt_lead(d):
    return f"🔥 לקוח חדש:\n👤 שם: {d.get('name','לא צוין')}\n🔧 שירות: {d.get('service','לא צוין')}\n📍 מיקום: {d.get('location','לא צוין')}\n📞 טלפון: {d.get('phone','לא צוין')}\n📝 תיאור: {d.get('description','לא צוין')}"

def fmt_bug(d):
    return f"🔴 תקלה חדשה:\n📌 נושא: {d.get('title','לא צוין')}\n🔴 חומרה: {d.get('severity','לא צוין')}\n👤 מדווח ע\"י: {d.get('reported_by','לא צוין')}\n📝 תיאור: {d.get('description','לא צוין')}"

def fmt_lovable(d):
    return f"🔵 בקשה חדשה:\n🪡 פיצ'ר: {d.get('feature','לא צוין')}\n🔵 עדיפות: {d.get('priority','לא צוין')}\n👤 מבקש: {d.get('requested_by','לא צוין')}\n📝 פרטים: {d.get('details','לא צוין')}"

def fmt_matchmaking(d):
    return f"🟣 הצעה חדשה:\n👤 שם: {d.get('name','לא צוין')}\n🎂 גיל: {d.get('age','לא צוין')}\n📍 מיקום: {d.get('location','לא צוין')}\n📞 טלפון: {d.get('phone','לא צוין')}\n📝 תיאור: {d.get('description','לא צוין')}"

def handle(bot_key, formatter):
    data = request.get_json() if request.is_json else request.form.to_dict()
    if not data:
        return jsonify({"status": "error"}), 400
    send_telegram(BOTS[bot_key]["token"], formatter(data))
    return jsonify({"status": "ok"}), 200

@app.route("/webhook/leads", methods=["POST"])
def leads(): return handle("leads", fmt_lead)

@app.route("/webhook/bugs", methods=["POST"])
def bugs(): return handle("bugs", fmt_bug)

@app.route("/webhook/lovable", methods=["POST"])
def lovable(): return handle("lovable", fmt_lovable)

@app.route("/webhook/matchmaking", methods=["POST"])
def matchmaking(): return handle("matchmaking", fmt_matchmaking)

@app.route("/health", methods=["GET"])
def health(): return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    print("🚀 Klik Agent פועל על פורט 5000")
    app.run(host="0.0.0.0", port=5000, debug=False)