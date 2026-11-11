"""All site content: the guide, well-being page, checklist and default samples.

The text comes from content.json. Edit the guide text there.
Announcements, timeline dates and stage dates can also be edited by staff
on the Staff page; the values here are only the starting samples.
"""
import html as _html
import json
import os
import re

SITE_NAME = "ScholarConnect"

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "content.json"), encoding="utf-8") as f:
    _RAW = json.load(f)

# Pages other than guide chapters that content can link to
PAGE_PATHS = {"home": "/", "guide": "/guide", "checklist": "/checklist", "wellbeing": "/wellbeing",
              "feedback": "/feedback", "thanks": "/thanks"}

CHAPTER_IDS = [c["id"] for c in _RAW["CHAPTERS"]]


def route(link):
    """Turn a link name (chapter id or page name) into a URL inside the app."""
    link = (link or "").strip()
    if not link:
        return ""
    if link.startswith("http"):
        return link
    if link in CHAPTER_IDS:
        return f"/guide?ch={link}"
    return PAGE_PATHS.get(link, "")


def _fix_links(s):
    """Point in-page links (#packing) at the right Streamlit page, and drop
    the prototype's Copy button (it needs JavaScript, which Streamlit strips)."""
    s = re.sub(r'href="#([a-z-]+)"', lambda m: f'href="{route(m.group(1))}" target="_self"', s)
    s = re.sub(r'<button type="button" data-copy="[^"]*">Copy</button>', "", s)
    return s


def plain(s):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


CHAPTERS = []
for c in _RAW["CHAPTERS"]:
    c = dict(c)
    for k in ("intro", "outro"):
        if c.get(k):
            c[k] = _fix_links(c[k])
    if c.get("sections"):
        c["sections"] = [{"h": s["h"], "html": _fix_links(s["html"])} for s in c["sections"]]
    if c.get("faqs"):
        c["faqs"] = [{**q, "a": _fix_links(q["a"])} for q in c["faqs"]]
    CHAPTERS.append(c)
CHAPTER_BY_ID = {c["id"]: c for c in CHAPTERS}

TIPS = _RAW["TIPS"]
RESOURCES = _RAW["RESOURCES"]
CHECKLISTS = _RAW["CHECK"]
POLLS = [{k: v for k, v in p.items() if k != "base"} for p in _RAW["POLLS"]]
FORMS = _RAW["FORMS"]
# Stage-based forms stop showing after this date (YYYY-MM-DD). Always-on forms are not listed.
FORM_CLOSES = {"prearrival": "2027-01-25"}
SAMPLE_NOTES = _RAW["SAMPLE_NOTES"]
PHOTOS = _RAW["PHOTOS"]
EDMS = _RAW["EDMS"]

# ---- starting samples for staff-editable content ----
DEFAULT_STAGES = [{"name": s["name"], "start": s["start"], "end": s["end"]} for s in _RAW["STAGES"]]
DEFAULT_EVENTS = [{"date": e["date"], "label": e.get("label", ""), "title": e["title"], "link": e.get("go", "")}
                  for e in _RAW["EVENTS"]]
DEFAULT_ANNOUNCEMENTS = [{"date": a["date"], "title": a["title"], "body": a["body"], "link": a.get("go", ""),
                          "pinned": "yes" if a.get("pinned") else "no"} for a in _RAW["ANNS"]]

GREETINGS = "Selamat datang · Chào mừng · Maligayang pagdating · ยินดีต้อนรับ · 欢迎"

# ---- search index ----
INDEX = []
for c in CHAPTERS:
    for i, s in enumerate(c.get("sections") or []):
        INDEX.append({"ch": c["id"], "open": None, "where": c["title"], "head": s["h"] or c["title"], "text": plain(s["html"])})
    for i, q in enumerate(c.get("faqs") or []):
        INDEX.append({"ch": c["id"], "open": i, "where": c["title"], "head": q["q"], "text": plain(q["a"])})
INDEX.append({"ch": None, "page": "wellbeing", "open": None, "where": "Well-being", "head": "Your well-being matters!",
              "text": " ".join(TIPS)})


def search(q, limit=6):
    terms = [t for t in q.lower().split() if len(t) > 1]
    if not terms:
        return [], terms
    scored = []
    for e in INDEX:
        hay = (e["head"] + " " + e["text"]).lower()
        if all(t in hay for t in terms):
            scored.append((sum(3 if t in e["head"].lower() else 1 for t in terms), e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:limit]], terms


def snippet(text, terms, width=140):
    low = text.lower()
    at = next((low.find(t) for t in terms if low.find(t) >= 0), 0)
    start = max(0, at - 50)
    s = ("…" if start else "") + text[start:start + width] + ("…" if start + width < len(text) else "")
    s = _html.escape(s)
    for t in terms:
        s = re.sub("(" + re.escape(_html.escape(t)) + ")", r"<mark>\1</mark>", s, flags=re.I)
    return s
