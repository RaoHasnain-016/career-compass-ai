from functools import lru_cache
from html import unescape
import logging
import os
import re
from time import monotonic

import requests


logger = logging.getLogger(__name__)
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_SEARCH_INTERVAL_SECONDS = 600


def youtube_video_links(video_id: str):
    if not isinstance(video_id, str) or not _VIDEO_ID.fullmatch(video_id):
        return None
    return {
        "youtube_video_id": video_id,
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
    }


def search_youtube_videos(query: str, max_results: int = 5):
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key or api_key == "your_youtube_api_key_here":
        return []

    window = int(monotonic() // _SEARCH_INTERVAL_SECONDS)
    return _search_youtube_videos(query, max_results, window)


@lru_cache(maxsize=128)
def _search_youtube_videos(query: str, max_results: int, _window: int):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": os.environ["YOUTUBE_API_KEY"].strip(),
        "safeSearch": "strict",
        "videoEmbeddable": "true",
    }
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params=params,
            timeout=(2, 3),
            allow_redirects=False,
        )
        if response.status_code != 200:
            logger.info("YouTube learning search unavailable (HTTP %d)", response.status_code)
            return []
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        logger.info("YouTube learning search unavailable (%s)", type(error).__name__)
        return []

    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []

    videos = []
    for item in items:
        if not isinstance(item, dict):
            continue
        identity, snippet = item.get("id"), item.get("snippet")
        if not isinstance(identity, dict) or not isinstance(snippet, dict):
            continue
        links = youtube_video_links(identity.get("videoId"))
        title = unescape(str(snippet.get("title") or "")).strip()[:255]
        if links and title:
            videos.append({
                **links,
                "title": title,
                "channel_title": unescape(str(snippet.get("channelTitle") or "")).strip()[:150],
            })
    return videos[:max_results]
