from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader
import os
from operator import attrgetter

app = Flask(__name__)
CORS(app)

L = instaloader.Instaloader()

# Environment Variable se login (Safe)
def login_instagram():
    try:
        username = os.getenv("IG_USER")
        password = os.getenv("IG_PASS")
        if username and password:
            L.login(username, password)
            print("✅ Logged in successfully")
        else:
            print("⚠️ Running anonymously (Limited access)")
    except Exception as e:
        print(f"❌ Login Error: {e}")

login_instagram()

@app.route('/')
def home():
    return "🚀 InstaBackend Pro is Active"

@app.route('/api/get-reels', methods=['POST'])
def get_reels():
    data = request.json
    target_username = data.get('username')
    sort_mode = data.get('sort', 'latest') # latest, popular, oldest
    
    if not target_username:
        return jsonify({"error": "Username is required"}), 400

    try:
        # Check if full URL is pasted, extract username
        if "instagram.com" in target_username:
            target_username = target_username.split("instagram.com/")[1].split("/")[0]

        profile = instaloader.Profile.from_username(L.context, target_username)
        reels_list = []
        count = 0
        limit = 50 # Performance ke liye limit (Increase agar Render ka plan bada ho)

        # 1. Fetch Data
        posts_buffer = []
        for post in profile.get_posts():
            if post.is_video:
                posts_buffer.append(post)
                count += 1
            if count >= limit:
                break
        
        # 2. Sorting Logic (Python Side)
        if sort_mode == 'popular':
            # Sort by Likes (High to Low)
            posts_buffer.sort(key=attrgetter('likes'), reverse=True)
        elif sort_mode == 'oldest':
            # Sort by Date (Old to New)
            posts_buffer.sort(key=attrgetter('date'), reverse=False)
        else:
            # Latest (Default)
            pass 

        # 3. Create JSON
        for post in posts_buffer:
            reels_list.append({
                "id": post.shortcode, # Unique ID for tracking downloads
                "url": post.video_url,
                "thumbnail": post.url,
                "likes": post.likes,
                "views": post.video_view_count,
                "date": post.date.strftime("%Y-%m-%d"),
                "caption": post.caption[:60] + "..." if post.caption else ""
            })

        return jsonify({
            "success": True, 
            "username": target_username,
            "profile_pic": profile.profile_pic_url,
            "reels": reels_list
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
