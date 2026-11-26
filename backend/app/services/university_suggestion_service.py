"""Education-stage shortlists using a bounded set of official admissions sources."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from time import monotonic
from urllib.parse import urljoin, urlsplit

import httpx


@dataclass(frozen=True)
class Option:
    institution: str
    country: str
    title: str
    url: str
    level: str
    note: str
    fields: tuple[str, ...] = ()
    for_country: str = ""


PAKISTAN = "Pakistan"
UK = "United Kingdom"
US = "United States"
CANADA = "Canada"
AUSTRALIA = "Australia"
INDIA = "India"

FIELDS = (
    "technology", "data", "engineering", "health", "business", "design",
    "education", "law", "architecture", "media", "social_sciences", "science",
)

PATHWAYS = {
    "school": ("Senior secondary or technical training", "Choose your next school pathway",
        "Compare local senior-secondary streams or recognised technical training. Ask your school or board which subjects keep your chosen career paths open."),
    "senior_secondary": ("Bachelor's or foundation", "Plan your first university qualification",
        "Use the official course page to review required subjects, recognised qualifications, entry tests, language requirements, fees and current application dates."),
    "diploma": ("Degree progression or transfer", "Check how your diploma can lead to a degree",
        "Ask whether the university accepts your exact diploma and specialisation. Admission, advanced standing and credit transfer are separate decisions."),
    "undergraduate": ("Master's after bachelor's", "Explore postgraduate study after graduation",
        "Check the required completed degree, field, grades and experience. Clinical, legal, teaching and other regulated practice may require separate qualifying routes and registration."),
    "postgraduate": ("Doctorate or research", "Explore research and advanced study",
        "Compare project fit, supervision, funding and the specified qualification. Clinical and other regulated research qualifications do not automatically confer a licence."),
    "exploring": ("Choose an education stage", "Set your current education stage",
        "Complete the academic section of your profile to get a shortlist for your next qualification."),
}

_HEC_REGISTER = Option("Higher Education Commission", PAKISTAN, "Pakistan Qualification Register",
    "https://www.hec.gov.pk/english/services/universities/pqr/Pages/default.aspx", "Recognition register",
    "Confirm the degree, institution and campus before applying.")
_IBCC = Option("Inter Boards Coordination Commission", PAKISTAN, "SSC and HSSC qualification guidance",
    "https://ibcc.edu.pk/faqs/international-qualification-faqs/", "Senior secondary",
    "Check subject groups and equivalence for your Matric, Intermediate or A-level pathway.")
_TEVTA = Option("Punjab TEVTA", PAKISTAN, "Technical and vocational study calendar",
    "https://tevta.gop.pk/academic-calendar-2/", "Technical training",
    "Ask the local institute to confirm its programme, prior education requirements and intake.",
    ("engineering", "technology", "design", "architecture"))
_AU_PATHWAYS = Option("Study Australia", AUSTRALIA, "Pathways to university",
    "https://www.studyaustralia.gov.au/en/plan-your-studies/universities-and-higher-education/pathways-to-university", "Official advice",
    "Check which foundation or vocational pathway leads to the course you want.")
_UK_PATHWAYS = Option("British Council", UK, "Foundation pathway courses",
    "https://study-uk.britishcouncil.org/plan-studies/ways-learning/foundation-pathway-courses", "Official advice",
    "Review how foundation pathways work and what progression conditions apply.")

_SCHOOL_OPTIONS = (
    _TEVTA, _IBCC,
    Option("GOV.UK", UK, "Further education for ages 16 and 17",
        "https://www.gov.uk/further-education-courses/if-youre-16-or-17", "Post-16 education",
        "Check academic and technical options after GCSEs. Education rules differ across the UK."),
    Option("U.S. Department of Education", US, "High-school career and technical education",
        "https://ies.ed.gov/career-and-technical-education", "High-school pathways",
        "Ask your school about the high-school subjects and career pathways it offers."),
    Option("Government of Canada", CANADA, "Secondary-school education",
        "https://www.canada.ca/en/immigration-refugees-citizenship/services/settle-canada/education/school-types/elementary-secondary.html",
        "Secondary school", "Confirm graduation and course requirements with your province or territory."),
    Option("Study Australia", AUSTRALIA, "Australian secondary school pathways",
        "https://www.studyaustralia.gov.au/en_in/plan-your-studies/schools", "Senior secondary",
        "Ask your school about senior subjects and your state or territory qualification."),
    Option("Central Board of Secondary Education", INDIA, "Senior secondary curriculum",
        "https://cbseacademic.nic.in/curriculum_archive.html", "Classes XI and XII",
        "Use the current academic year and confirm subjects with your school or board."),
)

_BACHELOR_OPTIONS = (
    Option("Aga Khan University", PAKISTAN, "Bachelor of Medicine, Bachelor of Surgery",
        "https://www.aku.edu/admissions/mbbs/Pages/home.aspx", "Bachelor's",
        "Check the current science prerequisites, entrance process and clinical accreditation.", ("health",)),
    Option("Allama Iqbal Open University", PAKISTAN, "B.Ed. in Elementary Teacher Education",
        "https://www.aiou.edu.pk/b-ed-4-years-elementary-teacher-education", "Bachelor's",
        "Check qualification and teaching-practice requirements.", ("education",)),
    Option("Information Technology University", PAKISTAN, "BS Computer Science",
        "https://itu.edu.pk/admissions/bs-computer-science/", "Bachelor's",
        "Check the current mathematics prerequisites and admission route.", ("technology", "data")),
    Option("NUST", PAKISTAN, "Undergraduate subject and programme requirements",
        "https://nust.edu.pk/admissions/undergraduates/academic-qualification-required-for-different-ug-progammes/", "Bachelor's",
        "Compare programmes that accept your exact school subjects and qualification group.",
        ("engineering", "architecture", "technology", "data", "design", "media", "social_sciences", "science", "law", "business")),
    Option("LUMS", PAKISTAN, "Undergraduate programmes",
        "https://admission.lums.edu.pk/undergraduate-programmes", "Bachelor's",
        "Find the related programme and check the current entrance requirements.",
        ("business", "law", "technology", "data", "engineering", "science", "social_sciences")),
    Option("University of Manchester", UK, "Foundation and degree routes for applicants from Pakistan",
        "https://www.manchester.ac.uk/study/international/country-specific-information/pakistan/", "Foundation or bachelor's",
        "Use the route for your qualification. The university distinguishes Intermediate/HSC from A-level or IB entry.",
        ("technology", "data", "engineering", "health", "science", "business", "law", "social_sciences"), PAKISTAN),
    Option("University of Manchester", UK, "Undergraduate course finder",
        "https://www.manchester.ac.uk/study/undergraduate/courses/index.htm", "Bachelor's",
        "Check whether your qualification calls for a foundation year and what subjects are required.", FIELDS),
    Option("UNSW Sydney", AUSTRALIA, "Bachelor of Science (Computer Science)",
        "https://www.unsw.edu.au/study/undergraduate/bachelor-of-computer-science", "Bachelor's",
        "Review the international entry pathway and the computing specialisations.", ("technology", "data")),
    Option("UNSW Sydney", AUSTRALIA, "Bachelor of Engineering (Honours)",
        "https://www.unsw.edu.au/study/undergraduate/bachelor-of-engineering-honours", "Bachelor's",
        "Choose an engineering specialisation and check its mathematics and science preparation.", ("engineering",)),
    Option("UNSW Sydney", AUSTRALIA, "Bachelor of Architectural Studies",
        "https://www.unsw.edu.au/study/undergraduate/bachelor-of-architectural-studies", "Bachelor's",
        "Check the undergraduate entry route and the further qualifications required for registration.", ("architecture",)),
    Option("UNSW Sydney", AUSTRALIA, "Bachelor of Design",
        "https://www.unsw.edu.au/study/undergraduate/bachelor-of-design1", "Bachelor's",
        "Review the design majors and check whether the relevant admission pathway involves a portfolio.", ("design",)),
    Option("UNSW Sydney", AUSTRALIA, "University degree finder",
        "https://www.unsw.edu.au/study/find-a-degree-or-course", "Bachelor's",
        "Filter to undergraduate courses and open the international entry requirements.", FIELDS),
    Option("University of Toronto", CANADA, "Undergraduate programme finder",
        "https://www.utoronto.ca/academics/undergraduate-programs", "Bachelor's",
        "Review the campus and admission category. A related undergraduate field is distinct from a professional licence.", FIELDS),
    Option("Arizona State University", US, "Undergraduate major finder",
        "https://degrees.asu.edu/bachelors", "Bachelor's",
        "Check the equivalent school qualification and major-specific admission requirements.", FIELDS),
    Option("University of Delhi", INDIA, "Undergraduate admissions and programme bulletins",
        "https://admission.uod.ac.in/", "Bachelor's",
        "Open the undergraduate bulletin and check the applicant category, entrance requirements and intake.",
        ("technology", "data", "science", "education", "media", "social_sciences", "business", "law")),
)

_DIPLOMA_OPTIONS = (
    Option("NUST", PAKISTAN, "Engineering degrees with a listed DAE route",
        "https://nust.edu.pk/admissions/undergraduates/dae-eligibility-criteria/", "Bachelor's pathway",
        "Check the approved DAE specialisation-to-degree list and merit requirements.", ("engineering",), PAKISTAN),
    Option("Khwaja Fareed University of Engineering and Information Technology", PAKISTAN,
        "Programmes with a listed DAE route",
        "https://www.kfueit.edu.pk/index.php/dae-eligibility-criteria?main=624&parent=Admissions", "Bachelor's pathway",
        "Find the programme on the published DAE table and confirm that your specialisation is accepted.",
        ("technology", "data", "engineering", "science", "design", "education", "media", "social_sciences"), PAKISTAN),
    Option("Arizona State University", US, "International transfer applicant guidance",
        "https://admission.asu.edu/apply/international/transfer", "Transfer pathway",
        "Use this route only if your post-secondary study qualifies. Ask for a credit assessment for your intended major.", FIELDS),
    Option("University of Toronto", CANADA, "Requirements for international university or college students",
        "https://future.utoronto.ca/requirements-international-university-or-college", "Transfer pathway",
        "Ask whether your institution, completed studies and target admission category can be assessed.", FIELDS),
    Option("UNSW Sydney", AUSTRALIA, "Credit transfer and advanced standing",
        "https://www.unsw.edu.au/student/managing-your-studies/essentials/credit-transfer", "Transfer pathway",
        "Read the credit rules before assuming advanced entry. The course admission decision is separate.", FIELDS),
)

_MASTER_OPTIONS = (
    Option("Aga Khan University", PAKISTAN, "Pakistan health sciences admissions",
        "https://www.aku.edu/admissions/Pages/pakistan.aspx", "Master's",
        "Select a graduate health programme and check relevant degree and experience requirements.", ("health",)),
    Option("LUMS", PAKISTAN, "Graduate programmes",
        "https://admission.lums.edu.pk/graduate-programmes", "Master's",
        "Check the relevant programme's completed-degree and selection requirements.",
        ("education", "business", "law", "science", "technology", "data", "engineering", "social_sciences")),
    Option("NUST", PAKISTAN, "Master's programmes of study",
        "https://nust.edu.pk/admissions/masters/programs-of-study/", "Master's",
        "Confirm the accepted undergraduate discipline, campus and intake.",
        ("technology", "data", "engineering", "design", "architecture", "science", "health", "business", "social_sciences", "media")),
    Option("University of Manchester", UK, "MSc Data Science",
        "https://www.idsai.manchester.ac.uk/study/masters/msc-data-science/", "Master's",
        "Compare the degree pathways and their subject and quantitative prerequisites.", ("data",)),
    Option("University of Toronto", CANADA, "Public Health Sciences graduate programmes",
        "https://www.sgs.utoronto.ca/programs/public-health-sciences/", "Master's",
        "Compare MPH and MSc streams and check the experience and degree requirements.", ("health",)),
    Option("UNSW Sydney", AUSTRALIA, "Master of Architecture",
        "https://www.unsw.edu.au/study/postgraduate/master-of-architecture", "Master's",
        "Check your architectural qualification, design work requirements and accreditation route.", ("architecture",)),
    Option("UNSW Sydney", AUSTRALIA, "Master of Education",
        "https://www.unsw.edu.au/study/postgraduate/master-of-education", "Master's",
        "Check the entry pathway for your degree and experience and any separate teacher registration rules.", ("education",)),
    Option("Arizona State University", US, "MA Journalism",
        "https://degrees.asu.edu/masters-phd/major/ASU00/CSJRNMA/journalism-ma/", "Master's",
        "Review programme prerequisites, application materials and campus availability.", ("media",)),
    Option("University of Manchester", UK, "Master's course finder",
        "https://www.manchester.ac.uk/study/masters/courses/", "Master's",
        "Compare courses and check whether your completed bachelor's degree is accepted.", FIELDS),
    Option("University of Toronto", CANADA, "Graduate programme finder",
        "https://www.utoronto.ca/academics/graduate-programs", "Master's",
        "Filter to a master's programme and check the department's prerequisites and language requirements.", FIELDS),
    Option("UNSW Sydney", AUSTRALIA, "Postgraduate application guidance",
        "https://www.unsw.edu.au/study/how-to-apply/postgraduate", "Master's",
        "Use the degree finder alongside the international postgraduate admissions requirements.", FIELDS),
    Option("Arizona State University", US, "Graduate degree finder",
        "https://degrees.asu.edu/masters-phd", "Master's",
        "Filter to a master's programme and open the specific admission criteria.", FIELDS),
    Option("University of Delhi", INDIA, "Postgraduate admissions and programme bulletins",
        "https://admission.uod.ac.in/", "Master's",
        "Check the postgraduate bulletin and programme-specific applicant category and prerequisites.",
        ("technology", "data", "science", "education", "media", "social_sciences", "business", "law")),
)

_RESEARCH_OPTIONS = (
    Option("NUST", PAKISTAN, "Doctoral programmes",
        "https://nust.edu.pk/admissions/phd/phd-programmes-of-study/", "Doctorate",
        "Check the current list for your research area and prior qualification.",
        ("technology", "data", "engineering", "science", "business", "social_sciences")),
    Option("University of Manchester", UK, "Postgraduate research programme finder",
        "https://www.manchester.ac.uk/study/postgraduate-research/programmes/", "Doctorate",
        "Identify a research area and check funding, supervision and project eligibility.", FIELDS),
    Option("University of Toronto", CANADA, "Doctoral options in the graduate calendar",
        "https://sgs.calendar.utoronto.ca/graduate-programs-at-a-glance", "Doctorate",
        "Find an offering marked as doctoral and review graduate-unit requirements.", FIELDS),
    Option("Arizona State University", US, "Doctoral options in the graduate degree finder",
        "https://degrees.asu.edu/masters-phd", "Doctorate",
        "Filter to a doctorate in your intended research area.", FIELDS),
)

_OPTIONS = {
    "school": _SCHOOL_OPTIONS,
    "senior_secondary": _BACHELOR_OPTIONS,
    "diploma": _DIPLOMA_OPTIONS,
    "undergraduate": _MASTER_OPTIONS,
    "postgraduate": _RESEARCH_OPTIONS,
    "exploring": (),
}

_COUNTRY_ALIASES = {
    "pk": PAKISTAN, "gb": UK, "uk": UK, "usa": US, "us": US, "au": AUSTRALIA,
    **{country.casefold(): country for country in (PAKISTAN, UK, US, CANADA, AUSTRALIA, INDIA)},
}


def _recommendation_sources(country, stage):
    if stage == "school":
        return (_IBCC,) if country == PAKISTAN else ()
    if stage == "exploring":
        return ()
    sources = []
    if country == PAKISTAN:
        sources.append(_HEC_REGISTER)
    if stage in {"senior_secondary", "diploma"}:
        sources.extend((_AU_PATHWAYS, _UK_PATHWAYS))
    return tuple(sources)


def _choose_options(country, field, stage):
    candidates = [option for option in _OPTIONS[stage]
                  if (not option.fields or field in option.fields)
                  and (not option.for_country or option.for_country == country)]
    # More specific field coverage outranks a general directory. Ties keep the stable catalogue order.
    if stage != "school":
        candidates.sort(key=lambda option: len(option.fields) or len(FIELDS) + 1)
    domestic = [option for option in candidates if option.country == country][:4]
    if stage == "school" or not country:
        return domestic, []
    international = []
    countries = set()
    for option in candidates:
        if option.country != country and option.country not in countries:
            international.append(option)
            countries.add(option.country)
        if len(international) == 4:
            break
    return domestic, international


@dataclass(frozen=True)
class _PageCheck:
    attempted_at: float
    checked_at: str | None
    last_success: float | None
    reachable: bool


_FRESH_SECONDS = 6 * 60 * 60
_RETRY_SECONDS = 10 * 60
_STALE_SECONDS = 7 * 24 * 60 * 60
_MAX_PAGE_BYTES = 8 * 1024
_PAGE_TIMEOUT_SECONDS = 3.0
_PUBLIC_HOSTS = frozenset(
    urlsplit(option.url).hostname.removeprefix("www.")
    for option in [option for row in _OPTIONS.values() for option in row]
    + [_HEC_REGISTER, _AU_PATHWAYS, _UK_PATHWAYS]
)
_page_cache: dict[str, _PageCheck] = {}
_page_locks: dict[str, asyncio.Lock] = {}


def _allowed_url(url):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").removeprefix("www.")
        return (parts.scheme == "https" and host in _PUBLIC_HOSTS
                and parts.port in (443, None) and parts.username is None
                and parts.password is None and not parts.fragment)
    except ValueError:
        return False


async def _source_reachable(client, url):
    if not _allowed_url(url):
        return False
    original_host = urlsplit(url).hostname.removeprefix("www.")
    try:
        async with asyncio.timeout(_PAGE_TIMEOUT_SECONDS):
            for _ in range(3):
                if (not _allowed_url(url)
                        or urlsplit(url).hostname.removeprefix("www.") != original_host):
                    return False
                async with client.stream("GET", url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            return False
                        url = urljoin(url, location)
                        continue
                    if response.status_code != 200:
                        return False
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
                    if content_type not in {"text/html", "application/xhtml+xml"}:
                        return False
                    prefix = bytearray()
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        prefix.extend(chunk[:_MAX_PAGE_BYTES - len(prefix)])
                        if re.search(rb"<(?:!doctype\s+html|html\b|head\b)", prefix, re.I):
                            return True
                        if len(prefix) >= _MAX_PAGE_BYTES:
                            break
                    return False
    except (httpx.HTTPError, TimeoutError, ValueError):
        return False
    return False


def _cached_check(url, now):
    previous = _page_cache.get(url)
    if previous is None:
        return None
    ttl = _FRESH_SECONDS if previous.reachable else _RETRY_SECONDS
    if now - previous.attempted_at >= ttl:
        return None
    if previous.reachable:
        return "cached", previous.checked_at
    if previous.last_success is not None and now - previous.last_success <= _STALE_SECONDS:
        return "stale", previous.checked_at
    return "unavailable", None


async def _check_source(client, url):
    lock = _page_locks.setdefault(url, asyncio.Lock())
    async with lock:
        cached = _cached_check(url, monotonic())
        if cached is not None:
            return cached
        previous = _page_cache.get(url)
        reachable = await _source_reachable(client, url)
        now = monotonic()
        instant = datetime.now(timezone.utc).isoformat() if reachable else previous.checked_at if previous else None
        last_success = now if reachable else previous.last_success if previous else None
        _page_cache[url] = _PageCheck(now, instant, last_success, reachable)
        if reachable:
            return "verified", instant
        if last_success is not None and now - last_success <= _STALE_SECONDS:
            return "stale", instant
        return "unavailable", None


def _serialize(option, checks):
    status, checked_at = checks[option.url]
    return {
        "institution": option.institution, "country": option.country, "title": option.title,
        "url": option.url, "level": option.level, "note": option.note,
        "verification_status": status, "checked_at": checked_at,
    }


async def get_university_suggestions(country: str, field: str, stage: str) -> dict:
    """Rank stage-compatible study options and check their official links."""
    country_name = _COUNTRY_ALIASES.get((country or "").strip().casefold(), "")
    stage = stage if stage in PATHWAYS else "exploring"
    target_level, pathway, guidance = PATHWAYS[stage]
    if not country_name and stage != "exploring":
        guidance += " The shortlist currently covers Pakistan, the US, the UK, Canada, Australia and India. Use your local education authority for other countries."
    if field not in FIELDS and stage not in {"school", "exploring"}:
        guidance += " Choose a career direction in your profile to see a field-based shortlist."

    domestic, international = _choose_options(country_name, field, stage)
    sources = _recommendation_sources(country_name, stage)
    urls = list(dict.fromkeys(option.url for option in [*domestic, *international, *sources]))
    now = monotonic()
    checks = {url: _cached_check(url, now) for url in urls}
    pending = [url for url in urls if checks[url] is None]
    if pending:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_PAGE_TIMEOUT_SECONDS), follow_redirects=False,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
            headers={"User-Agent": "CareerCompassAI/1.0", "Accept": "text/html", "Accept-Encoding": "identity"},
        ) as client:
            results = await asyncio.gather(*(_check_source(client, url) for url in pending))
            checks.update(zip(pending, results))

    return {
        "stage": stage, "target_level": target_level, "pathway": pathway, "guidance": guidance,
        "domestic": [_serialize(option, checks) for option in domestic],
        "international": [_serialize(option, checks) for option in international],
        "sources": [_serialize(option, checks) for option in sources],
        "checked_at": max((instant for _, instant in checks.values() if instant), default=None),
    }
