from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Load API key from environment variable
RAPIDAPI_KEY = "15c4fd52c7msh07c0a2768c2bdd3p1f6b5djsn0f9257862e61"
if not RAPIDAPI_KEY:
    raise EnvironmentError("RAPIDAPI_KEY is not set. Please set it in your environment variables.")

def get_user_data(username):
    """Fetch user data from the Instagram API."""
    try:
        url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
        querystring = {"username_or_id_or_url": username}
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user data: {e}")
        return None

def get_recent_posts(username):
    """Fetch recent posts of the user from the Instagram API."""
    try:
        url = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"
        querystring = {"username_or_id_or_url": username}
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': "instagram-scraper-api2.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        posts = []

        if 'data' in data and 'items' in data['data']:
            posts = data['data']['items'][:10]  # Fetch the first 10 posts
            for post in posts:
                caption_info = post.get('caption', {})
                post['caption_text'] = caption_info.get('text', 'No caption text available')
                post['created_at'] = caption_info.get('created_at', 'Unknown time')
                del post['caption']  # Remove full caption data for brevity

        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recent posts: {e}")
        return []

def user_information_final(username):
    """Aggregate user profile and post data."""
    user_data = get_user_data(username)
    if not user_data:
        return {"error": f"Unable to fetch the data for the username: {username}"}
    
    # Extract basic user information
    data = user_data.get('data', {})
    user_info = {
        "Username": data.get("username", "N/A"),
        "Name": data.get("full_name", "N/A"),
        "Bio": data.get("biography", "N/A"),
        "Followers": data.get("follower_count", 0),
        "Following": data.get("following_count", 0),
        "NumberOfPosts": data.get("media_count", 0),
        "Verified": "Yes" if data.get("is_verified") else "No",
        "AccountPrivacy": "Private" if data.get("is_private") else "Public",
    }

    # Fetch and process recent posts
    posts = get_recent_posts(username)
    captions = [
        {
            "PostNumber": index + 1,
            "Caption": post.get("caption_text", "No captions available"),
            "Upload Time": post.get("created_at", "Unknown time"),
        }
        for index, post in enumerate(posts)
    ]

    return {
        "ProfileInfo": user_info,
        "Captions": captions,
    }

@app.route('/instagram', methods=['POST'])
def instagram():
    """Endpoint to process Instagram user data."""
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400

    user_data = user_information_final(username)
    if "error" in user_data:
        return jsonify({'error': user_data['error']}), 404

    return jsonify({'result': user_data})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
