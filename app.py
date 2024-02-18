from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import os
import requests
import json
from werkzeug.utils import secure_filename
import random
import string

app = Flask(__name__)
app.secret_key = os.urandom(24)

DISCORD_CLIENT_ID = '981268814308184084'
DISCORD_CLIENT_SECRET = '2f_evZqSy6KIyOOnHuK1pX2Dej4Rtvfc'
DISCORD_REDIRECT_URI = "http://sparkle2.pyropixle.com:25502/callback"

@app.route('/')
def index():
    user_data = session.get('user_data', {})
    user = user_data.get("username")
    return render_template('home.html', username= user)

@app.route('/login')
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=email%20identify")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    response = requests.post('https://discord.com/api/oauth2/token', data={
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'scope': 'email identify avatar'
    })
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        user_info = requests.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {data["access_token"]}'})
        user_data = user_info.json()

        session['user_data'] = user_data
        print(user_data)
        return redirect(url_for('index'))

    return 'Fehler beim Authentifizieren'

app.config['UPLOAD_FOLDER'] = 'E:\Other\Ember\static\images-user'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}  # Erlaubte Dateierweiterungen

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/get_user_data')
def get_user_data():
    return jsonify(session.get('user_data', {}))

@app.route('/get_posts')
def get_tweets():
    user_data = session.get('user_data', {})
    if user_data.get('id'):
        user_id = user_data['id']
    else:
        user_id = 0

    request = requests.get(url="http://sparkle2.pyropixle.com:25501/API/GET/feed",
                           params={"apikey": "1234567890", "keywords": "red", "userid": str(user_id), "length": "10"})
    posts = request.json()

    parsed_posts = []
    for post in posts:
        author_id = post.get("userid")
        author_name = post.get("username")
        avatar = post.get("avatar")
        author_avatar = f'https://cdn.discordapp.com/avatars/{author_id}/{avatar}.png'
        content = post.get("content")
        created = post.get("created")
        attachments = post.get("attachments")
        id = post.get("id")
        views = post.get("views")
        likes = post.get("likes")

        parsed_posts.append({
            "author_id": author_id,
            "author_name": author_name,
            "author_avatar": author_avatar,
            "content": content,
            "created": created,
            "attachments": attachments,
            "id": id,
            "views": views,
            "likes": likes
        })

    return {'tweets': parsed_posts}

@app.route('/create_post', methods=['POST'])
def create_post():
    user_data = session.get('user_data', {})
    user_id = user_data.get('id', 0)
    
    content = request.form.get('content')
    attachments = []

    attachment = request.files.get('attachment')
    if attachment:
        attachment_filename = secure_filename(attachment.filename)
        attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename)
        if os.path.exists(attachment_path):
            # Datei existiert bereits, füge zufällige 5-stellige Zahl hinzu
            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            attachment_filename = f"{os.path.splitext(attachment_filename)[0]}_{random_suffix}{os.path.splitext(attachment_filename)[1]}"
            attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename)
        attachment.save(attachment_path)
        attachments.append(attachment_path)
    
    user_data = session.get('user_data', {})
    if user_data.get('id'):
        user_id = user_data['id']
    else:
        user_id = 0  # Standardwert, wenn die Nutzer-ID nicht verfügbar ist
    if user_data.get("username"):
        username = user_data["username"]
    else:
        username = "UNKNOWN"

    if user_data.get("avatar"):
        avatar = user_data["avatar"]
    else:
        avatar = "UNKNOWN"

    attachments_param = ' '.join(attachments) if attachments else ''
    response = requests.post(url="http://sparkle2.pyropixle.com:25501/API/SEND/post",
                             params={"apikey": "1234567890", "userid": user_id, "content": content,
                                     "attachements": str(attachments_param), "username": str(username), "avatar": str(avatar)})

    if response.status_code == 200:
        return jsonify(success=True)
    else:
        return jsonify(success=False)

@app.route("/follow", methods=['POST'])
def follow_funktion():
    if 'user_data' not in session:
        # Handle session or user data as needed
        return "Session data not available"

    followed_username = request.form.get("followed_username")
    if not followed_username:
        return "Followed username not provided"

    userdata = session['user_data']
    following = userdata.get("username", "")
    followed = followed_username

    response= requests.get("http://sparkle2.pyropixle.com:25501/API/ACTION/user/follow",
                 params={"apikey": "1234567890", "followed": followed, "following": following})
    if response.status_code == 200:
        return "success"
    else:
        return "error"

@app.route('/profile.html')
def profile():
    username = request.args.get('username')
    user_data_response = requests.get(f"http://sparkle2.pyropixle.com:25501/API/get/user", params={"username": username, "apikey": "1234567890"})
    print(user_data_response.json())
    userdata = session.get('user_data', {})
    following = str(userdata.get("id", ""))  # Konvertiere in Zeichenkettenformat

    data = user_data_response.json()
    followedby = [str(follower) for follower in data["followedby"]]  # Konvertiere jeden Wert in Zeichenkettenformat
    profile_id = data["id"]
    profile_avatar = data["avatar"]
    if user_data_response.status_code == 200:
        if following in followedby:
            print("gefolgt!")
            return render_template('profile.html', user=data, isFollowing=True, profileid=profile_id, avatarhash=profile_avatar)

        else:
            print("nutzer folgt nicht")
            return render_template('profile.html', user=data, isFollowing=False, profileid=profile_id, avatarhash=profile_avatar)
    else:
        return "User not found"  
    

@app.route('/like_post', methods=['POST'])
def like_post():
    data = request.json
    tweet_id = data.get('tweet_id')
    tweet_user = data.get('username')
    response = requests.get(f"http://sparkle2.pyropixle.com:25501/API/ACTION/user/like", params={"username": tweet_user, "postid": tweet_id, "apikey": "1234567890"})

    if response.status_code == 200:
        print("success")
        return "success"
    else:
        return "error"

@app.route('/reply-post', methods=['POST'])
def reply_post():
    print("erhalten! /reply-post!")
    data = request.json
    print(data)
    try:
        
        # Extrahieren der Parameter aus dem JSON-Datenobjekt
        userid = data.get('userid')
        content = data.get('content')
        attachments = data.get('attachments')
        username = data.get('username')
        avatar = data.get('avatar')
        parentid = data.get('parentid')

        response = requests.get("http://sparkle2.pyropixle.com:25501/API/SEND/answer", params={"apikey": "1234567890", "userid": userid, "content": content,
                                     "attachements": str(attachments), "username": str(username), "avatar": str(avatar), "parentid": parentid})

        if response.status_code == 200:
            print("success")
            return jsonify({"success": True})
        else:
            print("error!")
            return jsonify({"success": False})
        
    except Exception as e:
        print(f"ERROR - {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=25502, debug=False)
