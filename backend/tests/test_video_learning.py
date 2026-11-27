import os
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.video_resource_model import VideoResource
from app.services import youtube_service
from app.services.video_learning_service import recommend_video_courses


class VideoLearningTests(TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        VideoResource.__table__.create(engine)
        self.db = self.enterContext(Session(engine))

    def save_video(self, video_id, skill="Communication", *, active=True):
        video = VideoResource(
            youtube_video_id=video_id, title="Saved lesson", video_url="https://example.invalid/",
            skill=skill, career_field="Business", status=active, is_free=True,
        )
        self.db.add(video)
        self.db.commit()

    def test_completed_skills_still_offer_publisher_lessons_without_a_key(self):
        with patch.dict(os.environ, {"YOUTUBE_API_KEY": ""}):
            videos = recommend_video_courses(self.db, "Data Analyst", "Data", ["Excel", "Communication"], [], live=True)
        self.assertEqual([video["skill"] for video in videos], ["excel", "communication"])
        self.assertEqual({video["source_type"] for video in videos}, {"starter"})
        self.assertEqual(videos[0]["video_url"], "https://www.youtube.com/watch?v=Vl0H-qTclOg")

    def test_cached_skill_matches_across_fields_and_uses_canonical_video_url(self):
        self.save_video("validYTId01", skill=" Communication ")
        self.save_video("invalidUrl!", skill="Communication")
        self.save_video("HAnw168huqA", active=False)
        with patch("app.services.video_learning_service.search_youtube_videos") as search:
            videos = recommend_video_courses(self.db, "Engineer", "Engineering", ["Communication"], ["Communication"], live=False)
        self.assertEqual([video["video_url"] for video in videos], ["https://www.youtube.com/watch?v=validYTId01"])
        search.assert_not_called()

    def test_saved_and_starter_lessons_work_with_cache_table_absent(self):
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        with Session(engine) as db:
            videos = recommend_video_courses(db, "Teacher", "Education", ["Presentation"], [], live=False)
        self.assertEqual(videos[0]["youtube_video_id"], "HAnw168huqA")

    def test_dashboard_skips_external_lookup_for_an_uncovered_skill(self):
        with patch("app.services.video_learning_service.search_youtube_videos") as search:
            videos = recommend_video_courses(self.db, "Architect", "Architecture", ["Project Management"], [], live=False)
        search.assert_not_called()
        self.assertEqual(videos, [])

    def test_one_live_search_returns_and_caches_unique_videos(self):
        video = {
            **youtube_service.youtube_video_links("validYTId01"),
            "title": "Project management lesson", "channel_title": "Example educator",
        }
        with patch("app.services.video_learning_service.search_youtube_videos", return_value=[video, video]) as search:
            videos = recommend_video_courses(
                self.db, "Architect", "Architecture", ["Project Management", "Creativity"],
                ["Project Management", "Creativity"], live=True,
            )
            saved = recommend_video_courses(self.db, "Engineer", "Engineering", ["Project Management"], [], live=False)
        search.assert_called_once_with("project management beginner tutorial Architect", max_results=3)
        self.assertEqual([video["source_type"] for video in videos], ["youtube"])
        self.assertEqual([video["source_type"] for video in saved], ["saved"])
        self.assertEqual(self.db.query(VideoResource).count(), 1)


class YouTubeSearchTests(TestCase):
    def setUp(self):
        youtube_service._search_youtube_videos.cache_clear()
        self.addCleanup(youtube_service._search_youtube_videos.cache_clear)

    def test_timeout_and_quota_response_leave_video_recommendations_available(self):
        with (
            patch.dict(os.environ, {"YOUTUBE_API_KEY": "synthetic"}),
            patch.object(youtube_service.requests, "get", side_effect=[requests.Timeout, Mock(status_code=403)]) as get,
        ):
            self.assertEqual(youtube_service.search_youtube_videos("Project management"), [])
            self.assertEqual(youtube_service.search_youtube_videos("Project management"), [])
            self.assertEqual(youtube_service.search_youtube_videos("Research skills"), [])
        self.assertEqual(get.call_count, 2)

    def test_search_checks_ids_and_titles_and_decodes_provider_text(self):
        response = Mock(status_code=200)
        response.json.return_value = {"items": [
            {"id": {"videoId": "validYTId01"}, "snippet": {"title": "Design &amp; layout", "channelTitle": "Publisher"}},
            {"id": {"videoId": "bad/?id"}, "snippet": {"title": "Invalid identifier"}},
            {"id": {"videoId": "validYTId02"}, "snippet": {}},
        ]}
        with (
            patch.dict(os.environ, {"YOUTUBE_API_KEY": "synthetic"}),
            patch.object(youtube_service.requests, "get", return_value=response) as get,
        ):
            videos = youtube_service.search_youtube_videos("Design")
        self.assertEqual([video["title"] for video in videos], ["Design & layout"])
        self.assertTrue(videos[0]["video_url"].startswith("https://www.youtube.com/watch?v="))
        self.assertEqual(get.call_args.kwargs["params"]["safeSearch"], "strict")
        self.assertFalse(get.call_args.kwargs["allow_redirects"])
