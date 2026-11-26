import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.services import university_suggestion_service as university


_STAMP = "2026-11-26T03:00:00+00:00"


class UniversitySuggestionTests(unittest.IsolatedAsyncioTestCase):
    async def suggestions(self, country, field, stage):
        with (
            patch.object(university.httpx, "AsyncClient", return_value=AsyncMock()),
            patch.object(university, "_check_source", new=AsyncMock(return_value=("cached", _STAMP))),
        ):
            return await university.get_university_suggestions(country, field, stage)

    async def test_matric_only_gets_next_school_and_technical_pathways(self):
        result = await self.suggestions("Pakistan", "engineering", "school")

        self.assertEqual(result["target_level"], "Senior secondary or technical training")
        self.assertEqual(result["international"], [])
        self.assertEqual({item["institution"] for item in result["domestic"]}, {
            "Inter Boards Coordination Commission", "Punjab TEVTA",
        })
        all_items = result["domestic"] + result["sources"]
        self.assertTrue(all("bachelor" not in item["level"].lower() for item in all_items))

    async def test_diploma_uses_conditional_transfer_paths_and_approved_dae_option(self):
        result = await self.suggestions("PK", "engineering", "diploma")

        self.assertEqual(result["domestic"][0]["institution"], "NUST")
        self.assertIn("specialisation", result["domestic"][0]["note"])
        self.assertTrue(result["international"])
        self.assertTrue(all(item["level"] == "Transfer pathway" for item in result["international"]))
        technology = await self.suggestions("Pakistan", "technology", "diploma")
        self.assertTrue(technology["domestic"][0]["institution"].startswith("Khwaja Fareed University"))
        unlisted = await self.suggestions("Pakistan", "health", "diploma")
        self.assertEqual(unlisted["domestic"], [])

    async def test_senior_secondary_study_options_are_ranked_by_field_and_country(self):
        technology = await self.suggestions("Pakistan", "technology", "senior_secondary")
        health = await self.suggestions("Pakistan", "health", "senior_secondary")

        self.assertEqual(technology["domestic"][0]["title"], "BS Computer Science")
        self.assertEqual(health["domestic"][0]["institution"], "Aga Khan University")
        self.assertTrue(any("Intermediate/HSC" in item["note"] for item in technology["international"]))
        self.assertTrue(all(item["country"] == "Pakistan" for item in technology["domestic"]))
        self.assertTrue(all(item["country"] != "Pakistan" for item in technology["international"]))
        self.assertEqual(technology["checked_at"], _STAMP)
        self.assertEqual(technology["domestic"][0]["verification_status"], "cached")

    async def test_in_progress_bachelor_and_postgraduate_have_distinct_targets(self):
        bachelor = await self.suggestions("Australia", "architecture", "undergraduate")
        postgraduate = await self.suggestions("Pakistan", "engineering", "postgraduate")

        self.assertEqual(bachelor["domestic"][0]["title"], "Master of Architecture")
        self.assertIn("after graduation", bachelor["pathway"])
        self.assertIn("registration", bachelor["guidance"])
        self.assertTrue(postgraduate["domestic"])
        self.assertTrue(all(item["level"] == "Doctorate" for item in postgraduate["domestic"]))

    async def test_unknown_education_or_country_does_not_assume_admission_options(self):
        with patch.object(university, "_check_source", new=AsyncMock()) as check:
            result = await university.get_university_suggestions("Unknown", "technology", "unknown")
        check.assert_not_awaited()
        self.assertEqual(result["stage"], "exploring")
        self.assertEqual(result["domestic"], [])
        self.assertEqual(result["international"], [])
        self.assertIsNone(result["checked_at"])

    async def test_fresh_cached_options_do_not_create_a_network_client(self):
        now = university.monotonic()
        cached = university._PageCheck(now, _STAMP, now, True)
        with (
            patch.dict(university._page_cache, {university._IBCC.url: cached}, clear=True),
            patch.object(university.httpx, "AsyncClient") as client,
        ):
            result = await university.get_university_suggestions("Pakistan", "health", "school")
        client.assert_not_called()
        self.assertEqual(result["domestic"][0]["verification_status"], "cached")


class OfficialPageCheckTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        university._page_cache.clear()
        university._page_locks.clear()
        self.url = university._HEC_REGISTER.url

    def tearDown(self):
        university._page_cache.clear()
        university._page_locks.clear()

    async def test_public_html_is_checked_without_following_cross_host_redirects(self):
        calls = []

        def handler(request):
            calls.append(request.url.host)
            if request.url.path == "/redirect":
                return httpx.Response(302, headers={"location": "https://example.org/redirect"})
            return httpx.Response(200, headers={"content-type": "text/html; charset=UTF-8"},
                                  content=b"<!doctype html><html><title>Admissions</title></html>")

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            self.assertTrue(await university._source_reachable(client, self.url))
            self.assertFalse(await university._source_reachable(client, "https://www.hec.gov.pk/redirect"))
            self.assertFalse(await university._source_reachable(client, "http://127.0.0.1/"))
        self.assertEqual(calls, ["www.hec.gov.pk", "www.hec.gov.pk"])

    async def test_refresh_cache_retains_verified_timestamp_on_source_outage(self):
        reach = AsyncMock(side_effect=[True, False, False])
        with patch.object(university, "_source_reachable", new=reach), patch.object(university, "monotonic") as ticks:
            ticks.return_value = 100
            status, stamp = await university._check_source(None, self.url)
            self.assertEqual(status, "verified")
            self.assertIsNotNone(stamp)

            ticks.return_value = 101
            self.assertEqual(await university._check_source(None, self.url), ("cached", stamp))

            ticks.return_value = 100 + university._FRESH_SECONDS + 1
            self.assertEqual(await university._check_source(None, self.url), ("stale", stamp))

            ticks.return_value = 100 + university._STALE_SECONDS + 1
            self.assertEqual(await university._check_source(None, self.url), ("unavailable", None))
        self.assertEqual(reach.await_count, 3)

    async def test_non_html_errors_are_unavailable(self):
        def handler(_):
            return httpx.Response(200, headers={"content-type": "application/json"}, json={"result": True})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            self.assertEqual(await university._check_source(client, self.url), ("unavailable", None))


if __name__ == "__main__":
    unittest.main()
