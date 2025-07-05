from flask import Flask, request, jsonify
from datetime import datetime
import threading, time, requests, os, json, logging
from byte import Encrypt_ID, encrypt_api  # تأكد أن ملف byte.py موجود

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# ====== إعدادات عامة ======
users_file = "users.json"
TOKEN = None
MAX_REQUESTS = 1200  # عدد الطلبات المرسلة

# ====== معلومات المطور ======
def get_author_info():
    return "API BY : XZANJA"

# ====== جلب التوكن من API خارجي ======
def fetch_token():
    url = "https://aditya-jwt-v11op.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            token = response.json().get("token", "").strip()
            if token.count('.') == 2:
                return token
    except Exception as e:
        app.logger.error("🚫 خطأ أثناء جلب التوكن: %s", str(e))
    return None

# ====== تحديث التوكن كل ثانية ======
def update_token():
    global TOKEN
    while True:
        TOKEN = fetch_token()
        time.sleep(1)

# ====== إرسال طلب صداقة ======
def send_friend_request(uid):
    if not TOKEN:
        return "🚫 Token غير متوفر."

    try:
        encrypted_id = Encrypt_ID(uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        encrypted_payload = encrypt_api(payload)

        url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB49",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(encrypted_payload)),
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
            "Host": "clientbp.ggblueshark.com",
            "Connection": "close",
            "Accept-Encoding": "gzip, deflate, br"
        }

        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        return response.status_code == 200
    except Exception as e:
        return f"🚫 خطأ أثناء الإرسال: {e}"

# ====== حفظ عدد الطلبات لكل UID ======
def save_user(uid, count=0):
    users = {}
    if os.path.exists(users_file):
        try:
            with open(users_file, "r") as f:
                users = json.load(f)
        except:
            users = {}

    users[uid] = {
        "start_time": int(time.time()),
        "requests_sent": count
    }

    with open(users_file, "w") as f:
        json.dump(users, f)

# ====== بدء إرسال الطلبات بشكل تلقائي ======
def start_spam_thread(uid):
    def spam_loop():
        count = 0
        while count < MAX_REQUESTS:
            result = send_friend_request(uid)
            if result is True:
                count += 1
                app.logger.info(f"✅ [{uid}] تم إرسال الطلب رقم {count}")
            else:
                app.logger.warning(f"⚠️ [{uid}] فشل في الطلب رقم {count + 1}: {result}")

            save_user(uid, count)
            time.sleep(1.5)  # كل 1.5 ثانية

    threading.Thread(target=spam_loop, daemon=True).start()

# ====== نقطة الوصول: المقبرة ======
@app.route("/M9bra-add", methods=["GET", "POST"])
def add_uid():
    try:
        uid = request.args.get("uid") if request.method == "GET" else request.json.get("uid")

        if not uid:
            return jsonify({
                "error": "UID مطلوب",
                "developer": get_author_info()
            }), 400

        save_user(uid, 0)
        start_spam_thread(uid)

        return jsonify({
            "status": "✅ تم وضع UID داخل المقبرة بنجاح!",
            "UID": uid,
            "max_requests": MAX_REQUESTS,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "developer": get_author_info()
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "developer": get_author_info()
        }), 500

# ====== تشغيل التطبيق ======
if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))