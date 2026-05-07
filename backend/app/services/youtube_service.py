import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_youtube_videos(query: str, max_results: int = 5):
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "your_youtube_api_key_here":
        return []

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "safeSearch": "strict",
        "videoEmbeddable": "true",
        "relevanceLanguage": "en",
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return []

    data = response.json()
    videos = []

    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})

        if not video_id:
            continue

        videos.append({
            "youtube_video_id": video_id,
            "title": snippet.get("title"),
            "channel_title": snippet.get("channelTitle"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
        })

    return videos