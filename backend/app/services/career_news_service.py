"""Retrieve public career and training updates from a fixed set of publishers."""

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import logging
import re
from time import monotonic
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx


logger = logging.getLogger(__name__)
_TIMEOUT_SECONDS = 4
_MAX_FEED_BYTES = 750_000
_MAX_FEED_ENTRIES = 1500
_MAX_FEED_ITEMS = 36
_LOOKBACK = timedelta(days=60)
_MAX_STALE = timedelta(hours=24)
_REFRESH_SECONDS = 5 * 60
_RETRY_SECONDS = 2 * 60
_ATOM = "{http://www.w3.org/2005/Atom}"
_VOCATIONAL_STAGES = ("senior_secondary", "diploma")


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    host: str
    path_prefix: str
    country: str
    format: str = "xml"


_SOURCES = (
    # Official index: https://www.onetcenter.org/rss.html
    FeedSource(
        "O*NET Resource Center", "https://www.onetcenter.org/rss/whatsnew.xml",
        "www.onetcenter.org", "/whatsnew.html", "United States",
    ),
    # Official index: https://www.gov.uk/government/organisations/department-for-education
    FeedSource(
        "UK Department for Education",
        "https://www.gov.uk/government/organisations/department-for-education.atom",
        "www.gov.uk", "/government/", "United Kingdom",
    ),
    # Official index: https://www.gov.uk/government/organisations/skills-england
    FeedSource(
        "Skills England on GOV.UK", "https://www.gov.uk/government/organisations/skills-england.atom",
        "www.gov.uk", "/government/", "United Kingdom",
    ),
    # Official index: https://www.hec.gov.pk/english/HECAnnouncements/Pages/Announcements.aspx
    FeedSource(
        "Higher Education Commission Pakistan",
        "https://www.hec.gov.pk/english/HECAnnouncements/_api/web/lists/getbytitle(%27Pages%27)/items"
        "?$top=30&$select=Title,Created,ArticleStartDate,Expiry_x0020_Date,AnnouncementType,FileRef,SeoMetaDescription"
        "&$orderby=Created%20desc",
        "www.hec.gov.pk", "/english/HECAnnouncements/Pages/", "Pakistan", format="hec_json",
    ),
)

_FIELDS = {
    "technology": r"software|cybersecurity|cyber security|computer science|cloud computing|web development|information technolog(?:y|ies)|IT support|CS and IT|programmers?",
    "data": r"data analy(?:sis|tics|sts?)|data science|machine learning|artificial intelligence|statisticians?|statistical modell?ing",
    "engineering": r"engineer(?:s|ing)?|electrical|electronics|manufacturing|mechanical|construction|technicians? and trades workers",
    "health": r"health ?care|nurs(?:e|es|ing)|medical|medicine|pharmac(?:y|ists?)|health and wellbeing",
    "business": r"account(?:ant|ants|ancy|ing)|finance|marketing|entrepreneur(?:s|ship)?|business administration|sales workers",
    "design": r"graphic design|user experience|UI design|UX design|visual design|creative arts",
    "education": r"teach(?:ers?|ing)|tutors?|early years education|lesson planning|schools? workforce",
    "law": r"lawyers?|legal services|legal profession|paralegals?|law school",
    "architecture": r"architects?|architecture|built environment|urban plan(?:ning|ners?)",
    "media": r"journalism|journalists?|broadcasting|news media|media production|reporters?",
    "social_sciences": r"psycholog(?:y|ists?)|sociolog(?:y|ists?)|social work(?:ers?)?|community services|social assistance",
    "science": r"scientists?|lab(?:oratory)? technic(?:ian|ians|al)|biolog(?:y|ists?)|chemistry|environmental science|physicists?",
}
_FIELD_PATTERNS = {
    name: re.compile(rf"\b(?:{terms})\b", re.IGNORECASE) for name, terms in _FIELDS.items()
}
# Specific occupation headlines can narrow a department match. General field
# updates keep an empty list so they still reach students following that field.
_OCCUPATIONS = {
    "software": r"software engineer(?:s|ing)?|software developers?|web developers?|programmers?",
    "cybersecurity": r"cyber[ -]?security|information security analysts?",
    "it_support": r"IT support|computer support specialists?|help desk technicians?",
    "data": r"data analysts?|data scientists?|statisticians?",
    "civil_engineering": r"civil engineer(?:s|ing)?",
    "electrical_engineering": r"electrical engineer(?:s|ing)?|electrical technicians?",
    "medicine": r"doctors?|physicians?|medical practitioners?",
    "nursing": r"nurses?|nursing",
    "pharmacy": r"pharmacists?|pharmacy technicians?",
    "lab_technology": r"(?:medical |clinical )?lab(?:oratory)? technicians?",
    "accounting": r"accountants?|accounting technicians?|bookkeepers?",
    "psychology": r"psychologists?",
    "teaching": r"teachers?|teaching assistants?|tutors?",
    "law": r"lawyers?|solicitors?|barristers?|paralegals?",
    "architecture": r"architects?|architectural technologists?",
    "graphic_design": r"graphic designers?",
    "journalism": r"journalists?|reporters?",
    "environmental_science": r"environmental scientists?",
}
_OCCUPATION_PATTERNS = {
    name: re.compile(rf"\b(?:{terms})\b", re.IGNORECASE) for name, terms in _OCCUPATIONS.items()
}
_CAREER = re.compile(
    r"\b(?:career(?:s| pathways)?|occupations?|occupational|workforce|employment|labou?r market|"
    r"job ads?|job growth|job openings|hiring|skills needs|skills shortages|staff shortages|"
    r"recruitment difficulties|outlook handbook|in[- ]demand roles)\b", re.IGNORECASE,
)
_TRAINING = re.compile(r"\b(?:apprentice\w*|technical training|vocational|skills training|work-based learning)\b", re.IGNORECASE)
_POSTGRAD = re.compile(
    r"\b(?:post[- ]?graduate|master(?:['’]s|s)? degree|master['’]s|ph\.?\s*d\.?|doctorate|doctoral|mba|m\.?sc\.?)\b",
    re.IGNORECASE,
)
_BACHELOR = re.compile(
    r"\b(?:bachelor(?:['’]s|s)?|undergraduate|integrated degree|degree apprenticeship|bsc|beng|bba|bfa|llb|mbbs)\b",
    re.IGNORECASE,
)
_STUDY_AD = re.compile(
    r"\b(?:admissions?|scholarships?|applications? (?:open|close)|apply (?:now|by|for)|"
    r"intakes?|tuition|degree (?:program(?:me)?s?|courses?))\b", re.IGNORECASE,
)
_JUNK = re.compile(r"\b(?:casino\w*|gambling|sports betting|bonus codes?|betting odds)\b", re.IGNORECASE)
_XML_DTD = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_SAFE_ENCODED_SEPARATOR = re.compile(r"%(?:0[0-9a-f]|1[0-9a-f]|2f|5c|7f)", re.IGNORECASE)
_PUBLICATION_PREFIX = re.compile(
    r"^(?:official statistics|research|guidance|policy paper|transparency data):\s*", re.IGNORECASE,
)
_HIGHER_APPRENTICESHIP = re.compile(r"\bhigher(?:[- ]level)? apprenticeships?\b|\blevels?\s*[67]\b", re.IGNORECASE)
_HEC_RESULT = re.compile(
    r"\b(?:answer keys?|results?|merit lists?|nomination status|successful candidates|recruitment tests?)\b",
    re.IGNORECASE,
)
_HEC_GRADUATE = re.compile(r"\b(?:HAAT|HAT[- ](?:General|MS|PhD)|M\.?Phil)\b", re.IGNORECASE)
_HEC_UNDERGRADUATE = re.compile(r"\bUSAT\b", re.IGNORECASE)
_HEC_ACCREDITATION = re.compile(r"\b(?:verify accreditation|accreditation advisory)\b", re.IGNORECASE)


class _PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def _plain_text(value):
    parser = _PlainTextParser()
    parser.feed((value or "")[:8000])
    parser.close()
    return " ".join(" ".join(parser.text).split())


def _shorten(value, limit):
    if len(value) <= limit:
        return value
    return value[:limit].rsplit(" ", 1)[0].rstrip() + "…"


def _article_url(raw, source):
    if not raw or len(raw) > 1500 or re.search(r"[\\\s\x00-\x1f\x7f]", raw):
        return None
    try:
        parsed = urlsplit(raw)
        if parsed.scheme != "https" or parsed.netloc != source.host:
            return None
        path = parsed.path
        if _SAFE_ENCODED_SEPARATOR.search(path) or any(c in {".", ".."} for c in unquote(path).split("/")):
            return None
        if source.path_prefix.endswith("/"):
            if not path.startswith(source.path_prefix) or path.rstrip("/") == source.path_prefix.rstrip("/"):
                return None
        elif path != source.path_prefix:
            return None
        if source.host == "www.gov.uk" and not path.startswith(
            ("/government/news/", "/government/publications/", "/government/statistics/")
        ):
            return None
        fragment = parsed.fragment if source.host == "www.onetcenter.org" else ""
        return urlunsplit(("https", source.host, path.rstrip("/"), "", fragment))
    except ValueError:
        return None


def _published_at(value):
    if not value or len(value) > 100:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError, OverflowError):
            return None
    try:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _fields(title, summary):
    fields = [name for name, terms in _FIELD_PATTERNS.items() if terms.search(title)]
    if not fields:
        fields = [name for name, terms in _FIELD_PATTERNS.items() if terms.search(summary)]
    return fields


def occupation_topics(title):
    """Find positively named occupations without treating a whole field as a role."""
    return [name for name, pattern in _OCCUPATION_PATTERNS.items() if pattern.search(title or "")]


def _classify(title, summary):
    title = _PUBLICATION_PREFIX.sub("", title)
    full = f"{title} {summary}"
    if _JUNK.search(full):
        return None

    fields = _fields(title, summary)
    if _STUDY_AD.search(full):
        return None
    if _POSTGRAD.search(full):
        return fields, ["undergraduate", "postgraduate"]
    if _BACHELOR.search(full):
        return fields, ["senior_secondary", "undergraduate"]
    if _TRAINING.search(full):
        # In England, levels 6 and 7 can be bachelor's and master's equivalent.
        # Unspecified "higher" apprenticeships are not a next-stage alert.
        if _HIGHER_APPRENTICESHIP.search(full):
            return fields, ["undergraduate", "postgraduate"]
        return fields, list(_VOCATIONAL_STAGES)
    if _CAREER.search(full):
        return fields, []
    return None


def _classify_hec_announcement(title, summary):
    full = f"{title} {summary}"
    if _JUNK.search(full) or _HEC_RESULT.search(title):
        return None
    if not (_STUDY_AD.search(full) or _HEC_ACCREDITATION.search(full)):
        return None

    # HEC's HAT-General and HAAT tests correspond to graduate admission.
    # Some scholarship headlines omit the level. Leave those out.
    if _POSTGRAD.search(full) or _HEC_GRADUATE.search(full):
        return _fields(title, summary), ["undergraduate", "postgraduate"]
    if _BACHELOR.search(full) or _HEC_UNDERGRADUATE.search(full):
        return _fields(title, summary), ["senior_secondary", "undergraduate"]
    if _HEC_ACCREDITATION.search(full):
        return _fields(title, summary), ["senior_secondary", "undergraduate", "postgraduate"]
    return None


def _read_entries(root):
    if root.tag == "rss":
        channel = root.find("channel")
        if channel is None:
            raise ValueError("RSS feed has no channel")
        for item in channel.iterfind("item"):
            yield (item.findtext("title"), item.findtext("description"), item.findtext("link"), item.findtext("pubDate"), None)
        return

    if root.tag == f"{_ATOM}feed":
        for item in root.iterfind(f"{_ATOM}entry"):
            link = next((node.get("href") for node in item.iterfind(f"{_ATOM}link")
                         if node.get("rel", "alternate") == "alternate"), None)
            yield (
                item.findtext(f"{_ATOM}title"), item.findtext(f"{_ATOM}summary"), link,
                item.findtext(f"{_ATOM}published") or item.findtext(f"{_ATOM}updated"), None,
            )
        return

    raise ValueError("Unexpected career feed format")


def _read_hec_entries(document, source):
    parsed = json.loads(document)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("value"), list):
        raise ValueError("Unexpected HEC announcements format")
    for item in parsed["value"]:
        if not isinstance(item, dict) or item.get("AnnouncementType") != "Current Announcements":
            continue
        file_ref = item.get("FileRef")
        if not isinstance(file_ref, str) or not file_ref.startswith(source.path_prefix):
            continue
        filename = file_ref.removeprefix(source.path_prefix)
        if not re.fullmatch(r"[^/\\?#]+\.aspx", filename, flags=re.IGNORECASE):
            continue
        raw_url = f"https://{source.host}{quote(file_ref, safe='/%-._~')}"
        title = item.get("Title")
        summary = item.get("SeoMetaDescription")
        date = item.get("ArticleStartDate") or item.get("Created")
        expiry = item.get("Expiry_x0020_Date")
        if any(value is not None and not isinstance(value, str) for value in (title, summary, date, expiry)):
            continue
        yield (title, summary, raw_url, date, expiry)


def _parse_feed(raw, source, now):
    if len(raw) > _MAX_FEED_BYTES:
        raise ValueError("Career feed exceeded size limit")
    # Decode before looking for DTD or entity syntax so alternate encodings
    # cannot bypass the XML validation.
    document = raw.decode("utf-8-sig")
    if source.format == "hec_json":
        entries = _read_hec_entries(document, source)
        classify = _classify_hec_announcement
    else:
        if _XML_DTD.search(document):
            raise ValueError("DTD and entity declarations are not supported")
        entries = _read_entries(ElementTree.fromstring(document))
        classify = _classify

    articles = {}
    for index, (raw_title, raw_summary, raw_url, raw_date, raw_expiry) in enumerate(entries):
        if index == _MAX_FEED_ENTRIES:
            break
        published = _published_at(raw_date)
        if published is None or not now - _LOOKBACK <= published <= now:
            continue
        expiry = _published_at(raw_expiry)
        if raw_expiry and (expiry is None or expiry <= now):
            continue
        url = _article_url(raw_url, source)
        title = _plain_text(raw_title)
        if not url or not title:
            continue
        summary = _plain_text(raw_summary)
        classification = classify(title, summary)
        if classification is None:
            continue

        fields, stages = classification
        item = {
            "id": f"news-{sha256(url.encode()).hexdigest()[:32]}",
            "title": _shorten(title, 180),
            "summary": _shorten(summary, 450),
            "url": url,
            "source": source.name,
            "country": source.country,
            "published_at": published.isoformat(),
            "fields": fields,
            "stages": stages,
            "occupations": occupation_topics(title),
        }
        if expiry:
            item["expires_at"] = expiry.isoformat()
        previous = articles.get(item["id"])
        if previous is None or previous["published_at"] < item["published_at"]:
            articles[item["id"]] = item

    return sorted(articles.values(), key=lambda item: item["published_at"], reverse=True)[:_MAX_FEED_ITEMS]


async def _fetch_feed(client, source):
    media_types = {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}
    headers = None
    if source.format == "hec_json":
        media_types = {"application/json"}
        headers = {"Accept": "application/json;odata=nometadata"}
    try:
        async with asyncio.timeout(_TIMEOUT_SECONDS):
            async with client.stream("GET", source.url, headers=headers) as response:
                response.raise_for_status()
                media_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
                if media_type not in media_types:
                    raise ValueError("Response was not a feed")
                if response.headers.get("content-encoding", "identity").lower() != "identity":
                    raise ValueError("Feed used an unexpected content encoding")
                body = bytearray()
                async for chunk in response.aiter_raw():
                    if len(body) + len(chunk) > _MAX_FEED_BYTES:
                        raise ValueError("Career feed exceeded size limit")
                    body.extend(chunk)
        checked_at = datetime.now(timezone.utc)
        return checked_at, _parse_feed(body, source, checked_at)
    except (TimeoutError, httpx.HTTPError, ValueError, ElementTree.ParseError) as error:
        logger.info("Career feed unavailable: %s (%s)", source.name, type(error).__name__)
        return None


class _CareerFeedCache:
    def __init__(self, sources=_SOURCES):
        self.sources = sources
        self._last_results = {}
        self._fresh_sources = set()
        self._refresh_lock = asyncio.Lock()
        self._refresh_at = 0

    async def _refresh_if_due(self):
        if monotonic() < self._refresh_at:
            return
        async with self._refresh_lock:
            if monotonic() < self._refresh_at:
                return
            async with httpx.AsyncClient(
                follow_redirects=False,
                timeout=_TIMEOUT_SECONDS,
                trust_env=False,
                headers={
                    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                    "Accept-Encoding": "identity",
                },
            ) as client:
                results = await asyncio.gather(*(_fetch_feed(client, source) for source in self.sources))
            self._fresh_sources = set()
            for source, result in zip(self.sources, results):
                if result is not None:
                    self._last_results[source] = result
                    self._fresh_sources.add(source)
            interval = _REFRESH_SECONDS if len(self._fresh_sources) == len(self.sources) else _RETRY_SECONDS
            self._refresh_at = monotonic() + interval

    async def get(self):
        await self._refresh_if_due()
        now = datetime.now(timezone.utc)
        available = {source: result for source, result in self._last_results.items()
                     if now - result[0] <= _MAX_STALE}
        checked_at = max((checked for checked, _ in available.values()), default=None)
        live = any(source in self._fresh_sources for source in available)
        stale = any(source not in self._fresh_sources for source in available)
        earliest = (now - _LOOKBACK).isoformat()
        now_iso = now.isoformat()
        articles = {item["id"]: item for _, items in available.values()
                    for item in items if item["published_at"] >= earliest
                    and ("expires_at" not in item or item["expires_at"] > now_iso)}
        return {
            "items": deepcopy(sorted(articles.values(), key=lambda item: item["published_at"], reverse=True)),
            "checked_at": checked_at.isoformat() if checked_at else None,
            "status": "stale" if stale else "live" if live else "unavailable",
            "sources": [
                {
                    "name": source.name,
                    "country": source.country,
                    "status": ("live" if source in self._fresh_sources else "stale") if source in available else "unavailable",
                }
                for source in self.sources
            ],
        }


_cache = _CareerFeedCache()


async def get_career_news():
    """Return a bounded public feed snapshot shared by all student requests."""
    return await _cache.get()
