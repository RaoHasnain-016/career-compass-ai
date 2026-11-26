"""Tests for publisher parsing, stage filtering, and shared career-news caching."""

import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
import unittest
from unittest.mock import AsyncMock, patch
from xml.etree import ElementTree

import httpx

from app.services import career_news_service as news


NOW = datetime(2026, 11, 26, 10, 0, tzinfo=timezone.utc)


def rss(*entries):
    root = ElementTree.Element("rss", version="2.0")
    channel = ElementTree.SubElement(root, "channel")
    for title, summary, url, date in entries:
        entry = ElementTree.SubElement(channel, "item")
        for tag, value in (
            ("title", title), ("description", summary), ("link", url),
            ("pubDate", format_datetime(date) if date else None),
        ):
            if value:
                ElementTree.SubElement(entry, tag).text = value
    return ElementTree.tostring(root)


class CareerNewsParsingTests(unittest.TestCase):
    def test_official_career_articles_are_deduped_sorted_and_attributed(self):
        source = news._SOURCES[0]
        updated = "https://www.onetcenter.org/whatsnew.html#20261125"
        body = rss(
            ("Software jobs outlook", "Old summary", updated, NOW - timedelta(days=2)),
            ("Nursing careers", "Clinical workforce needs", "https://www.onetcenter.org/whatsnew.html#nursing", NOW - timedelta(days=3)),
            ("Software jobs outlook", "<p>Growth in software occupations.</p><script>hidden()</script>", updated, NOW),
        )

        first, second = news._parse_feed(body, source, NOW)

        self.assertEqual(first["fields"], ["technology"])
        self.assertEqual(first["stages"], [])
        self.assertEqual(first["country"], "United States")
        self.assertEqual(first["source"], source.name)
        self.assertEqual(first["summary"], "Growth in software occupations.")
        self.assertEqual(first["published_at"], NOW.isoformat())
        self.assertEqual(second["fields"], ["health"])
        self.assertNotEqual(first["id"], second["id"])

    def test_apprenticeships_are_for_next_stage_learners_and_degree_ads_are_excluded(self):
        source = news._SOURCES[1]
        body = rss(
            ("Electrical engineering technician", "Revised apprenticeship standards", f"https://{source.host}/government/news/electrical", NOW),
            ("Digital user experience (integrated degree)", "Apprenticeship applications open", f"https://{source.host}/government/news/digital", NOW),
            ("Cybersecurity apprenticeship", "Under revision", f"https://{source.host}/guidance/security-in-revision", NOW),
            ("Civil engineer", "Future apprenticeship standard", f"https://{source.host}/government/news/civil", NOW + timedelta(days=1)),
        )

        item, = news._parse_feed(body, source, NOW)
        self.assertEqual(item["fields"], ["engineering"])
        self.assertEqual(item["stages"], ["senior_secondary", "diploma"])
        self.assertEqual(item["country"], "United Kingdom")

    def test_degree_levels_hidden_in_summaries_still_restrict_audience(self):
        source = news._SOURCES[0]
        body = rss(
            ("Career prospects for psychologists", "This update is for doctoral learners.", f"https://{source.host}/whatsnew.html#graduate", NOW),
            ("Computing degree outcomes", "The cohort completed a bachelor's degree.", f"https://{source.host}/whatsnew.html#undergrad", NOW),
            ("Scholarships for data scientists", "Apply now", f"https://{source.host}/whatsnew.html#advert", NOW),
        )

        graduate, undergraduate = news._parse_feed(body, source, NOW)
        self.assertEqual(graduate["stages"], ["undergraduate", "postgraduate"])
        self.assertEqual(undergraduate["stages"], ["senior_secondary", "undergraduate"])

    def test_higher_apprenticeship_is_never_offered_to_diploma_or_school(self):
        source = news._SOURCES[1]
        body = rss(
            ("Engineering apprenticeship standards update", "New level 7 standards", f"https://{source.host}/government/news/level-7", NOW),
            ("Higher apprenticeships in education", "Advanced training", f"https://{source.host}/government/news/higher", NOW),
        )
        items = news._parse_feed(body, source, NOW)
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item["stages"], ["undergraduate", "postgraduate"])

    def test_rejects_missing_dates_old_articles_and_non_publisher_links(self):
        source = news._SOURCES[0]
        first = "https://www.onetcenter.org/whatsnew.html"
        body = rss(
            ("Career news", "", first + "#old", NOW - timedelta(days=90)),
            ("Career news", "", first + "#undated", None),
            ("Career news", "", "javascript:alert(1)", NOW),
            ("Career news", "", "https://www.onetcenter.org.example.com/whatsnew.html", NOW),
            ("Career news", "", "https://u@www.onetcenter.org/whatsnew.html", NOW),
            ("Career news", "", "http://www.onetcenter.org/whatsnew.html", NOW),
            ("Career news", "", "https://www.onetcenter.org/redirect.html", NOW),
            ("GamblING casino!", "Career options", first + "#junk", NOW),
            ("Minutes for the board", "Meeting attendance records", first + "#irrelevant", NOW),
        )

        self.assertEqual(news._parse_feed(body, source, NOW), [])

    def test_atom_uses_article_link_and_original_publication_when_present(self):
        source = news._SOURCES[2]
        body = b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Official Statistics: Teaching occupations in demand</title>
            <summary type="html">&lt;b&gt;Staff shortages&lt;/b&gt;</summary>
            <link rel="self" href="https://www.gov.uk/ignore"/>
            <link rel="alternate" href="https://www.gov.uk/government/statistics/occupations-in-demand?source=rss"/>
            <published>2026-11-23T08:00:00+00:00</published>
            <updated>2026-11-26T08:00:00+00:00</updated>
          </entry>
        </feed>"""
        item, = news._parse_feed(body, source, NOW)
        self.assertEqual(item["url"], "https://www.gov.uk/government/statistics/occupations-in-demand")
        self.assertEqual(item["published_at"], "2026-11-23T08:00:00+00:00")
        self.assertEqual(item["fields"], ["education"])

    def test_publisher_name_does_not_invent_a_career_match(self):
        source = news._SOURCES[0]
        body = rss((
            "Updated outlook information", "The Bureau of Labor Statistics published employment projections.",
            f"https://{source.host}/whatsnew.html#outlook", NOW,
        ))
        item, = news._parse_feed(body, source, NOW)
        self.assertEqual(item["fields"], [])

    def test_hec_announcements_stay_current_local_and_stage_specific(self):
        source = news._SOURCES[-1]

        def record(title, name, **overrides):
            return {
                "Title": title,
                "Created": "2026-11-20T15:34:13Z",
                "Expiry_x0020_Date": "2026-12-18T19:00:00Z",
                "AnnouncementType": "Current Announcements",
                "FileRef": f"{source.path_prefix}{name}.aspx",
                **overrides,
            }

        body = json.dumps({"value": [
            record("Admissions notice for HAT-General and HAAT-Subject", "graduate"),
            record("Bachelor's Computer Science scholarships", "undergraduate"),
            record("Foreign government scholarship programme", "unknown-level"),
            record("Answer keys for HAT-MS test", "answer-keys"),
            record("PhD scholarship", "expired", Expiry_x0020_Date="2026-11-24T18:00:00Z"),
            record("Master's scholarships", "past", AnnouncementType="Past Announcements"),
            record("Undergraduate admissions", "../another-folder"),
        ]}).encode()

        graduate, undergraduate = news._parse_feed(body, source, NOW)
        self.assertEqual(graduate["country"], "Pakistan")
        self.assertEqual(graduate["stages"], ["undergraduate", "postgraduate"])
        self.assertEqual(graduate["url"], f"https://{source.host}{source.path_prefix}graduate.aspx")
        self.assertEqual(graduate["expires_at"], "2026-12-18T19:00:00+00:00")
        self.assertEqual(undergraduate["fields"], ["technology"])
        self.assertEqual(undergraduate["stages"], ["senior_secondary", "undergraduate"])

    def test_xml_declarations_and_size_limits_are_enforced(self):
        source = news._SOURCES[0]
        xml = b'<!DOCTYPE rss [<!ENTITY surprise "bad">]><rss><channel></channel></rss>'
        with self.assertRaisesRegex(ValueError, "DTD"):
            news._parse_feed(xml, source, NOW)
        with self.assertRaisesRegex(ValueError, "size limit"):
            news._parse_feed(b" " * (news._MAX_FEED_BYTES + 1), source, NOW)


class _Body(httpx.AsyncByteStream):
    def __init__(self, *chunks):
        self.chunks = chunks

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


class CareerNewsFetchTests(unittest.IsolatedAsyncioTestCase):
    async def test_fixed_publisher_fetch_accepts_rss_without_student_data(self):
        source = news._SOURCES[0]
        observed = []

        def handle(request):
            observed.append((request.method, str(request.url), request.headers.get("authorization")))
            body = rss((
                "Civil engineering jobs outlook", "Workforce projections",
                f"https://{source.host}/whatsnew.html#civil", datetime.now(timezone.utc) - timedelta(minutes=1),
            ))
            return httpx.Response(200, headers={"Content-Type": "text/xml"}, stream=_Body(body))

        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
            checked, items = await news._fetch_feed(client, source)

        self.assertEqual(observed, [("GET", source.url, None)])
        self.assertTrue(checked)
        self.assertEqual(items[0]["fields"], ["engineering"])

    async def test_non_feed_response_and_overlarge_stream_fail_closed(self):
        source = news._SOURCES[0]
        bad_responses = [
            httpx.Response(200, headers={"Content-Type": "text/html"}, stream=_Body(b"<html>")),
            httpx.Response(200, headers={"Content-Type": "text/xml"}, stream=_Body(b" " * (news._MAX_FEED_BYTES + 1))),
            httpx.Response(302, headers={"Location": "https://different.example/"}),
            httpx.Response(200, headers={"Content-Type": "text/xml", "Content-Encoding": "gzip"}, stream=_Body(b"compressed")),
        ]
        for response in bad_responses:
            async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: response)) as client:
                self.assertIsNone(await news._fetch_feed(client, source))

    async def test_concurrent_users_share_refresh_and_stale_results_are_bounded(self):
        source = news._SOURCES[0]
        cached = news._CareerFeedCache((source,))
        now = datetime.now(timezone.utc)
        items = [{"id": "news-1", "fields": ["engineering"], "published_at": now.isoformat()}]

        with patch.object(news, "_fetch_feed", new=AsyncMock(return_value=(now, items))) as fetch:
            first, second = await asyncio.gather(cached.get(), cached.get())
            fetch.assert_awaited_once()
            self.assertEqual(first["status"], "live")
            self.assertEqual(first["checked_at"], now.isoformat())
            first["items"][0]["fields"].clear()
            self.assertEqual(second["items"][0]["fields"], ["engineering"])
            self.assertEqual((await cached.get())["items"][0]["fields"], ["engineering"])

        with patch.object(news, "_fetch_feed", new=AsyncMock(return_value=None)) as fetch:
            cached._refresh_at = 0
            self.assertEqual((await cached.get())["status"], "stale")
            self.assertEqual((await cached.get())["status"], "stale")
            fetch.assert_awaited_once()

            cached._last_results[source] = (now - timedelta(days=2), items)
            expired = await cached.get()
            self.assertEqual(expired["status"], "unavailable")
            self.assertEqual(expired["items"], [])
            self.assertIsNone(expired["checked_at"])

    async def test_expiring_hec_notice_is_removed_even_during_cache_interval(self):
        source = news._SOURCES[-1]
        cached = news._CareerFeedCache((source,))
        now = datetime.now(timezone.utc)
        item = {
            "id": "news-1",
            "published_at": (now - timedelta(days=1)).isoformat(),
            "expires_at": (now - timedelta(seconds=1)).isoformat(),
        }
        with patch.object(news, "_fetch_feed", new=AsyncMock(return_value=(now, [item]))):
            snapshot = await cached.get()
        self.assertEqual(snapshot["status"], "live")
        self.assertEqual(snapshot["items"], [])


if __name__ == "__main__":
    unittest.main()
