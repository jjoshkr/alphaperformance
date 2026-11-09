#!/usr/bin/env python3
"""Injury watch v2: football injury news -> structured facts -> rehab content -> alert.

Pipeline (every run):
  1. collect   Google News RSS queries + direct RSS feeds (+ API-Football if a key is set)
  2. filter    football only (league/club dictionary), injury headlines only, drop duplicates
  3. extract   player / club / league / body part / severity / duration
               - Claude API (structured output) when ANTHROPIC_API_KEY is set
               - keyword rules otherwise
  4. remember  docs/injuries/state.json keeps what was already seen (per player + body part)
  5. alert     new items -> Telegram (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID), with rehab phase,
               drills and demo-video links
  6. report    docs/injuries/YYYY-MM-DD.md, latest.md, latest.json

Usage:
  python tools/injury_watch/injury_watch.py             # live
  python tools/injury_watch/injury_watch.py --sample    # offline test with sample_feed.xml
  python tools/injury_watch/injury_watch.py --no-notify # never send Telegram
Only the Anthropic SDK is an optional dependency (pip install anthropic); everything else is stdlib.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT_DIR = ROOT / "docs" / "injuries"
KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (compatible; alpha-performance-injury-watch)"}

BODY_PARTS = ["hamstring", "knee_acl", "knee_other", "ankle", "groin", "calf", "achilles", "quad",
              "hip", "foot", "back", "shoulder", "concussion", "muscle_general"]
LEAGUES = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]

# ---------------------------------------------------------------- rules (fallback extraction)
BODY_PART_RULES = [
    ("concussion", r"concussion|head injury|head knock|skull|facial fracture"),
    ("achilles", r"achilles"),
    ("hamstring", r"hamstring|back of (the|his|her) thigh"),
    ("knee_acl", r"\bacl\b|cruciate|meniscus|\bmcl\b|\blcl\b|\bpcl\b|patella"),
    ("groin", r"groin|adductor|hernia"),
    ("calf", r"\bcalf\b|soleus|gastrocnemius"),
    ("quad", r"\bquad|rectus femoris|\bthigh\b"),
    ("ankle", r"ankle|syndesmosis"),
    ("foot", r"metatarsal|\bfoot\b|\btoe\b|plantar|\bheel\b"),
    ("hip", r"\bhip\b|labrum|labral"),
    ("back", r"\bback injury\b|\bback problem\b|lumbar|spine|spinal|\bdisc\b"),
    ("shoulder", r"shoulder|collarbone|clavicle|\barm\b|elbow|wrist"),
    ("knee_other", r"\bknee\b"),
    ("muscle_general", r"muscle|muscular"),
]
HARD_SEVERE = r"rupture|ruptured|fracture|fractured|broken|surgery|operation|rest of the season|season over|season-ending"
SOFT_SEVERE = r"\btorn\b|\btear\b|long-term|months"
MINOR_WORDS = r"\bknock\b|minor|precaution|slight|doubt|fitness test|late fitness|assessed|scare"
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "twelve": 12, "several": 3, "a few": 3, "couple of": 2, "a": 1}
DURATION_RE = re.compile(
    r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|several|a few|couple of|a)\s*(?:to|-|–)?\s*(\d+)?\s*(day|week|month)s?", re.I)
INJURY_SIGNALS = r"injur|out for|ruled out|sidelined|\bmiss|\bblow\b|setback|surgery|fracture|\btear\b|\btorn\b|strain|\bknock\b|limp|stretcher|withdraw|doubt|scare|crisis"
NOT_INJURY = (r"\breturn|back in training|fit again|recovered|comeback|available again|injury-free|transfer|\bsigns?\b|\bloan\b"
              r"|sack|appoint|boost|all-clear|green light|injuries & suspensions|injuries and suspensions"
              r"|preview|prediction|lineups?|line-ups?|team news|emerged stronger|injury woes|injury record|injury crisis"
              r"|\bnasa\b|wonderkid|joining|survive|hard-fought|things to look|\bfpl\b|fantasy|injury-time|stoppage-time"
              r"|opens door|opportunity for|chance for|\b\d+-\d+\b|player ratings|talking points")
PLAYER_RE = re.compile(
    r"\b([A-Z][a-zA-Z'’\-]+(?: (?:de|van|der|di|da|van der|von)?\s?[A-Z][a-zA-Z'’\-]+){0,2})\s+"
    r"(?:injury|suffers|ruled out|out for|sidelined|to miss|faces|limps|set to miss|could miss|will miss|injured|stretchered|withdraws|undergoes|out with|a doubt)",
)


def rule_body_part(text):
    t = text.lower()
    for key, pat in BODY_PART_RULES:
        if re.search(pat, t):
            return key
    return "unknown"


def rule_duration_weeks(text):
    m = DURATION_RE.search(text)
    if not m:
        return None, None
    n1, n2, unit = m.group(1).lower(), m.group(2), m.group(3).lower()
    n = int(n1) if n1.isdigit() else NUMBER_WORDS.get(n1, 1)
    if n2:
        n = int(n2)
    weeks = {"day": n / 7, "week": n, "month": n * 4.3}[unit]
    return round(weeks, 1), m.group(0)


def rule_severity(text, body_part):
    t = text.lower()
    weeks, phrase = rule_duration_weeks(t)
    if re.search(HARD_SEVERE, t) or body_part in ("knee_acl", "achilles"):
        return "severe", weeks, phrase
    if weeks is not None:
        return ("minor" if weeks < 2 else "moderate" if weeks <= 8 else "severe"), weeks, phrase
    if re.search(SOFT_SEVERE, t):
        return "severe", None, phrase
    if re.search(MINOR_WORDS, t):
        return "minor", None, phrase
    return "unknown", None, phrase


PLAYER_STOP = {"is", "why", "how", "will", "can", "does", "the", "star", "news", "report", "update", "latest",
               "premier", "league", "la", "liga", "serie", "ligue", "bundesliga", "champions", "europa", "injury",
               "manchester", "united", "city", "real", "madrid", "bayern", "munich", "arsenal", "chelsea", "liverpool",
               "barcelona", "juventus", "inter", "milan", "napoli", "roma", "dortmund", "psg", "marseille", "lyon",
               "atletico", "tottenham", "newcastle", "everton", "villa", "aston", "leipzig", "leverkusen"}


COMMON_WORDS = {"fresh", "major", "latest", "breaking", "weekend", "season", "preview", "opponent", "watch", "final",
                "series", "club", "team", "coach", "boss", "manager", "striker", "winger", "defender", "midfielder",
                "keeper", "goalkeeper", "captain", "forward", "player", "players", "squad", "crisis", "woes", "news",
                "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "january", "february",
                "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
                "world", "cup", "nations", "international", "derby", "clash", "match", "game", "things", "bosses",
                "england", "france", "spain", "germany", "italy", "brazil", "argentina", "portugal", "korea",
                "dutch", "french", "spanish", "german", "italian", "english", "fulham", "palace", "forest",
                "things", "concern", "double", "triple", "key", "big", "huge", "another", "second", "first",
                "ruled", "out", "confirms", "confirm", "confirmed", "dealt", "blow", "injury", "injured", "injuries",
                "sidelined", "suffers", "suffered", "faces", "doubt", "update", "issues", "gives", "setback", "scare",
                # body parts and injury words that headlines capitalise
                "hamstring", "tear", "torn", "knee", "ankle", "groin", "calf", "achilles", "thigh", "quad", "hip", "foot",
                "back", "shoulder", "concussion", "muscle", "muscular", "ligament", "tendon", "fracture", "absence",
                # outlets, squads, filler
                "evening", "standard", "yahoo", "sports", "sport", "usmnt", "england", "germany", "squad", "roster",
                "off", "despite", "five", "four", "three", "six", "official", "exclusive", "report", "live", "legend",
                "captain", "goalkeeper", "star", "ace", "boss", "chief", "owner", "workload", "defends"}
# "Rodri injury", "Zaccagni ruled out", "Baleba Doubt", "Joelinton out"
SURNAME_AFTER = re.compile(
    r"\b([A-Z][a-zA-Z\-]{3,}(?: [A-Z][a-zA-Z\-]{2,})?)\s+"
    r"(?i:injury(?! (?:update|news|latest|table|list|round-?up))|injured|ruled out|out\b|sidelined|blow|setback|suffers|suffered|"
    r"limps|stretchered|to miss|will miss|could miss|faces|a doubt|doubt|undergoes|has\b|set for|picks up|"
    r"on (?:his|her) injury)")
# "update on Guirassy", "blow for Calvert-Lewin", "issues Serhou Guirassy update", "Barcelona confirms Rodri"
SURNAME_BEFORE = re.compile(
    r"(?i:update on|news on|blow for|concern over|concern for|worry over|fears over|fears for|scare for|setback for|"
    r"without|loses?|confirms?|issues|gives|provides|delivers|on)\s+([A-Z][a-zA-Z\-]{3,}(?: [A-Z][a-zA-Z\-]{2,})?)")


def _clean_name(tokens):
    bad = lambda t: t.lower() in PLAYER_STOP or t.lower() in COMMON_WORDS
    while tokens and bad(tokens[0]):
        tokens = tokens[1:]
    while tokens and bad(tokens[-1]):
        tokens = tokens[:-1]
    if not tokens or any(bad(t) for t in tokens):
        return None
    if len(tokens) == 1 and len(tokens[0]) < 4:
        return None
    return " ".join(tokens[-3:] if len(tokens) > 3 else tokens)


def rule_player(text):
    text = re.sub(r"[’']s\b", "", text)  # "Musiala's injury" -> "Musiala injury"
    m = PLAYER_RE.search(text)
    if m:
        name = _clean_name(m.group(1).strip().split())
        if name and " " in name:
            return name
    for pat in (SURNAME_BEFORE, SURNAME_AFTER):
        for m in pat.finditer(text):
            name = _clean_name(m.group(1).strip().split())
            if name:
                return name
    return None


def player_key(name):
    """Same player whether written 'Calvert-Lewin' or 'Dominic Calvert-Lewin': key on the surname."""
    return re.sub(r"[^a-z]", "", name.split()[-1].lower()) if name else ""


def find_player(i):
    """Player name from the headline first, then the snippet, then the article body."""
    for text in (i.get("title", ""), i.get("snippet", "")):
        name = rule_player(text) if text else None
        if name:
            return name
    body = (i.get("body") or "")[:800]
    name = rule_player(body) if body else None
    if name and (" " in name or body.count(name) >= 2):
        return name
    return None


def looks_like_injury(text):
    t = text.lower()
    return bool(re.search(INJURY_SIGNALS, t)) and not re.search(NOT_INJURY, t)


# ---------------------------------------------------------------- league / football filter
def detect_league(text, src):
    """Return league name from club or league words in the text, else None."""
    t = text.lower()
    for league, aliases in src["league_aliases"].items():
        if any(a in t for a in aliases):
            return league
    for league, clubs in src["clubs"].items():
        for c in clubs:
            if re.search(r"\b" + re.escape(c.lower()) + r"\b", t):
                return league
    return None


def is_not_football(text, src):
    t = text.lower()
    return any(re.search(p, t) for p in src["not_football"])


# ---------------------------------------------------------------- collecting
def fetch(url, timeout=20, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def google_news_url(query, hours_back):
    days = max(1, round(hours_back / 24))
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:{days}d", "hl": "en", "gl": "US", "ceid": "US:en"})


def parse_rss(xml_bytes, feed_name):
    items = []
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip()
        desc = html.unescape(re.sub(r"<[^>]+>", " ", it.findtext("description") or "")).strip()
        pub = it.findtext("pubDate")
        source = (it.findtext("source") or "").strip()
        if feed_name == "Google News" and " - " in title:
            title, src_in_title = title.rsplit(" - ", 1)
            source = source or src_in_title.strip()
        try:
            when = parsedate_to_datetime(pub) if pub else None
            if when is not None and when.tzinfo is None:  # some feeds omit the timezone
                when = when.replace(tzinfo=timezone.utc)
        except Exception:
            when = None
        items.append({"title": title.strip(), "link": link, "snippet": desc[:300],
                      "source": source or feed_name, "feed": feed_name, "published": when})
    return items


def fetch_article_body(link, max_chars=1500):
    """Plain text of the article's first paragraphs. Google News links are redirects we can't follow; skip them."""
    if not link or "news.google.com" in link:
        return ""
    try:
        raw = fetch(link, timeout=12).decode("utf-8", "ignore")
    except Exception:
        return ""
    raw = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|aside).*?</\1>", " ", raw)
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", raw)
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x)) for x in paras)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def collect_api_football(src, errors):
    """Structured injuries from API-Football, if a key is configured."""
    key = os.environ.get("API_FOOTBALL_KEY")
    if not key or not src["api_football"].get("enabled_if_key"):
        return []
    now = datetime.now(timezone.utc)
    season = now.year if now.month >= 7 else now.year - 1
    out = []
    for league, lid in src["api_football"]["league_ids"].items():
        try:
            url = f"https://v3.football.api-sports.io/injuries?league={lid}&season={season}"
            data = json.loads(fetch(url, headers={"x-apisports-key": key}))
            if data.get("errors"):
                errors.append(f"API-Football {league}: {data['errors']}")
                continue
            for row in data.get("response", []):
                p, t, pl = row.get("player", {}), row.get("team", {}), row.get("player", {})
                reason = pl.get("reason") or ""
                title = f"{p.get('name')} ({t.get('name')}) - {reason} - {pl.get('type')}"
                out.append({"title": title, "link": "https://www.api-football.com", "snippet": reason,
                            "source": "API-Football", "feed": "API-Football", "published": now,
                            "league": league, "player": p.get("name"), "club": t.get("name"),
                            "structured": True})
        except Exception as e:
            errors.append(f"API-Football {league}: {e}")
    return out


def collect(src, sample_path=None):
    errors, items = [], []
    hours_back = src["hours_back"]
    if sample_path:
        items = parse_rss(Path(sample_path).read_bytes(), "Google News")
        for i in items:  # sample titles carry "[League]" prefixes
            m = re.match(r"\[(.+?)\]\s*(.*)", i["title"])
            if m:
                i["league_hint"], i["title"] = m.group(1), m.group(2)
    else:
        for q in src["google_news_queries"]:
            try:
                items += parse_rss(fetch(google_news_url(q, hours_back)), "Google News")
            except Exception as e:
                errors.append(f"Google News '{q}': {e}")
        for name, url in src["rss_feeds"].items():
            try:
                items += parse_rss(fetch(url), name)
            except Exception as e:
                errors.append(f"{name}: {e}")
        items += collect_api_football(src, errors)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    seen_titles, kept = set(), []
    for i in items:
        if i["published"] and i["published"] < cutoff and not sample_path:
            continue
        text = f"{i['title']} {i.get('snippet', '')}"
        if not i.get("structured"):
            if not looks_like_injury(i["title"]):
                continue
            if is_not_football(text, src):
                continue
            league = i.get("league_hint") or detect_league(text, src)
            if not league:
                continue
            i["league"] = league
        key = re.sub(r"[^a-z0-9]", "", i["title"].lower())[:70]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        i["title_key"] = key
        kept.append(i)
    kept.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return kept, errors


# ---------------------------------------------------------------- extraction
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "is_football_injury": {"type": "boolean",
                                           "description": "true only for a men's or women's association football (soccer) player injury report"},
                    "is_new_injury": {"type": "boolean",
                                      "description": "true if the headline reports a new injury or a diagnosis/timeline; false for returns, boosts, generic roundups, opinion"},
                    "player": {"type": ["string", "null"]},
                    "club": {"type": ["string", "null"]},
                    "league": {"type": "string", "enum": LEAGUES + ["other"]},
                    "body_part": {"type": "string", "enum": BODY_PARTS + ["unknown"]},
                    "severity": {"type": "string", "enum": ["minor", "moderate", "severe", "unknown"],
                                 "description": "minor <2 weeks, moderate 2-8 weeks, severe >8 weeks or surgery/rupture/fracture"},
                    "duration_weeks": {"type": ["number", "null"]},
                    "summary_en": {"type": "string", "description": "one neutral sentence in your own words, no copied text"}
                },
                "required": ["id", "is_football_injury", "is_new_injury", "player", "club", "league",
                             "body_part", "severity", "duration_weeks", "summary_en"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

EXTRACT_SYSTEM = (
    "You extract structured facts about football (soccer) player injuries from news headlines and snippets. "
    "Use only what the text states; put null when a field is not stated. Do not guess a body part from the club or player. "
    "Only the five leagues Premier League, La Liga, Bundesliga, Serie A, Ligue 1 count; players of those clubs injured on "
    "international duty still count under their club's league. Everything else (NFL, cricket, basketball, rugby) is not a football injury. "
    "player must be the injured player's full name (first and last) as the text identifies him; if the text names only a surname you can "
    "complete it only when the club context makes the player unambiguous, otherwise return the surname as written. "
    "If the text does not identify which player is injured, player must be null."
)


def extract_with_claude(items):
    """Batch-extract fields with Claude. Returns {index: fields} or None if unavailable."""
    if not os.environ.get("ANTHROPIC_API_KEY") or not items:
        return None
    try:
        import anthropic
    except ImportError:
        print("anthropic SDK not installed; using rule-based extraction", file=sys.stderr)
        return None
    client = anthropic.Anthropic()
    lines = []
    for n, i in enumerate(items):
        line = f"[{n}] HEADLINE: {i['title']}"
        if i.get("snippet"):
            line += f"\n    SNIPPET: {i['snippet']}"
        if i.get("body"):
            line += f"\n    ARTICLE: {i['body'][:700]}"
        lines.append(line)
    try:
        response = client.beta.messages.create(
            model=os.environ.get("INJURY_WATCH_MODEL") or "claude-opus-5-5",
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=EXTRACT_SYSTEM,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": EXTRACT_SCHEMA}},
            messages=[{"role": "user", "content": "Headlines:\n" + "\n".join(lines)}],
        )
    except anthropic.RateLimitError as e:
        print(f"Claude rate limited: {e}", file=sys.stderr)
        return None
    except anthropic.APIStatusError as e:
        print(f"Claude API error {e.status_code}: {e.message}", file=sys.stderr)
        return None
    except anthropic.APIConnectionError as e:
        print(f"Claude connection error: {e}", file=sys.stderr)
        return None
    if response.stop_reason == "refusal":
        print("Claude declined the extraction request", file=sys.stderr)
        return None
    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("Claude returned non-JSON; using rules", file=sys.stderr)
        return None
    return {row["id"]: row for row in data.get("items", []) if 0 <= row.get("id", -1) < len(items)}


def extract(items):
    by_claude = extract_with_claude(items)
    out = []
    for n, i in enumerate(items):
        text = f"{i['title']} {i.get('snippet', '')}"
        row = (by_claude or {}).get(n)
        if row:
            if not row["is_football_injury"] or not row["is_new_injury"]:
                continue
            i.update({
                "player": row["player"] or i.get("player"), "club": row["club"] or i.get("club"),
                "league": row["league"] if row["league"] in LEAGUES else i.get("league"),
                "body_part": row["body_part"], "severity": row["severity"],
                "duration_weeks": row["duration_weeks"], "summary_en": row["summary_en"],
                "extractor": "claude",
            })
            i["duration_phrase"] = rule_duration_weeks(text)[1]
        else:
            bp = rule_body_part(text)
            sev, weeks, phrase = rule_severity(text, bp)
            i.update({"player": i.get("player") or find_player(i), "club": i.get("club"),
                      "body_part": bp, "severity": sev, "duration_weeks": weeks, "duration_phrase": phrase,
                      "summary_en": None, "extractor": "rules"})
        if not i.get("league"):
            continue
        out.append(i)
    return out


# ---------------------------------------------------------------- state / dedupe
def entity_key(i):
    if i.get("player"):
        return player_key(i["player"]) + ":" + (i.get("body_part") or "unknown")
    return "title:" + i["title_key"]


def load_state(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen": {}}


def save_state(path, state):
    # keep 60 days of memory
    cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    state["seen"] = {k: v for k, v in state["seen"].items() if v.get("first_seen", "") >= cutoff}
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- content
SEVERITY_KO = {"minor": "경미 (2주 미만)", "moderate": "중간 (2~8주)", "severe": "중증 (8주 이상 / 수술 / 파열)", "unknown": "미상"}


def rehab_block(i, lib, videos):
    entry = lib.get(i.get("body_part"))
    if not entry:
        return None
    lead = {"minor": 2, "moderate": 1, "severe": 0, "unknown": 1}[i["severity"]]
    phase = entry["phases"][lead]
    drills = [{"name": d, "video": videos.get(d, "")} for d in phase["drills"]]
    who = i.get("player") or "A player"
    club = f" ({i['club']})" if i.get("club") else ""
    hook = f"{who}{club}: {entry['en']} injury. Here's what the comeback usually looks like."
    caption_en = (f"{hook}\n\nMost {entry['en']} rehab has 3 stages. This is the one that gets rushed:\n{phase['name']}\n"
                  + "\n".join(f"{n}. {d['name']}" for n, d in enumerate(drills, 1))
                  + "\n\n⚠️ General training education, not medical advice. Injured? See a physio first."
                  + "\n\n💬 Comment SPEED for my 6-week speed program (for healthy players).")
    caption_es = (f"{who}{club}: lesión de {entry['es']}. Así suele ser la vuelta.\n\n"
                  f"La rehabilitación de {entry['es']} tiene 3 fases. Esta es la que más se apresura:\n"
                  + "\n".join(f"{n}. {d['name']}" for n, d in enumerate(drills, 1))
                  + "\n\n⚠️ Educación general, no consejo médico. ¿Lesionado? Consulta a un fisio primero."
                  + "\n\n💬 Comenta VELOCIDAD para mi programa de velocidad de 6 semanas (para jugadores sanos).")
    return {"part_ko": entry["ko"], "part_en": entry["en"], "phase": phase["name"], "phase_goal": phase.get("goal", ""),
            "content_fit": entry.get("content_fit", 0), "content_fit_why": entry.get("content_fit_why", ""),
            "anatomy": entry.get("anatomy", {}), "drills": drills,
            "all_phases": entry["phases"], "content_angle": entry["content_angle"],
            "red_flags": entry["red_flags"], "caption_en": caption_en, "caption_es": caption_es}


# ---------------------------------------------------------------- telegram
def tg_escape(s):
    return html.escape(str(s or ""), quote=False)


def telegram_message(i):
    r = i["rehab"]
    dur = f" · {i['duration_phrase']}" if i.get("duration_phrase") else (
        f" · 약 {i['duration_weeks']}주" if i.get("duration_weeks") else "")
    head = f"🚑 <b>{tg_escape(i.get('player'))}</b>"
    if i.get("club"):
        head += f" · {tg_escape(i['club'])}"
    lines = [head + f" · {tg_escape(i['league'])}",
             f"부위: <b>{tg_escape(r['part_ko'] if r else '미분류')}</b> · 정도: {SEVERITY_KO[i['severity']]}{tg_escape(dur)}",
             f"📰 <a href=\"{tg_escape(i['link'])}\">{tg_escape(i['title'])}</a> ({tg_escape(i['source'])})"]
    if i.get("summary_en"):
        lines.append(f"<i>{tg_escape(i['summary_en'])}</i>")
    if r:
        a = r.get("anatomy") or {}
        if a:
            lines += ["", f"🧠 <b>어디·무슨 근육</b>", f"위치: {tg_escape(a.get('location', ''))}",
                      f"근육: {tg_escape(a.get('muscles', ''))}", f"집중: {tg_escape(a.get('focus', ''))}"]
        lines += ["", f"🏃 재활 단계: <b>{tg_escape(r['phase'])}</b>"]
        if r.get("phase_goal"):
            lines.append(f"목표: {tg_escape(r['phase_goal'])}")
        for n, d in enumerate(r["drills"], 1):
            v = f" — <a href=\"{tg_escape(d['video'])}\">영상</a>" if d["video"] else " — 영상 촬영 필요"
            lines.append(f"{n}. {tg_escape(d['name'])}{v}")
        lines += ["", f"🎯 각도: {tg_escape(r['content_angle'])}",
                  f"📈 채널 적합도: {'★' * r['content_fit']}{'☆' * (5 - r['content_fit'])} — {tg_escape(r['content_fit_why'])}",
                  f"⚠️ {tg_escape(r['red_flags'])}"]
    lines.append("\n<i>자동 초안 · 게시 전 원우 님 검토 · 의료 조언 아님</i>")
    return "\n".join(lines)


def discover_telegram_chats():
    """No TELEGRAM_CHAT_ID yet: find everyone who messaged the bot and tell them their chat id."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or os.environ.get("TELEGRAM_CHAT_ID"):
        return []
    token = token.strip()
    me = json.loads(fetch(f"https://api.telegram.org/bot{token}/getMe", timeout=20)).get("result", {})
    print(f"Telegram bot: @{me.get('username')} ({me.get('first_name')})")
    info = json.loads(fetch(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=20)).get("result", {})
    if info.get("url"):
        print(f"Telegram webhook is set ({info['url']}); getUpdates would be blocked, deleting it")
        fetch(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=20)
    data = json.loads(fetch(f"https://api.telegram.org/bot{token}/getUpdates?limit=100", timeout=20))
    updates = data.get("result", [])
    print(f"Telegram getUpdates: ok={data.get('ok')} updates={len(updates)} "
          f"types={sorted({k for u in updates for k in u if k != 'update_id'})}")
    chats = {}
    for u in updates:
        msg = (u.get("message") or u.get("edited_message") or u.get("channel_post")
               or u.get("my_chat_member") or u.get("chat_member") or {})
        chat = msg.get("chat") or {}
        if chat.get("id"):
            chats[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name") or ""
    for cid, name in chats.items():
        text = (f"✅ AlphaBot 연결 확인\n\n이 대화방의 ID: <code>{cid}</code>\n\n"
                "GitHub 저장소 → Settings → Secrets and variables → Actions 에\n"
                "이름 <b>TELEGRAM_CHAT_ID</b>, 값 위 숫자로 등록하면 부상 알림이 여기로 옵니다.")
        body = urllib.parse.urlencode({"chat_id": cid, "text": text, "parse_mode": "HTML"}).encode()
        try:
            urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body, headers=UA), timeout=20)
        except Exception as e:
            print(f"Telegram setup message to {cid} failed: {e}", file=sys.stderr)
    print(f"Telegram chat ids found: {list(chats) or 'none (send the bot a message first)'}")
    return list(chats)


def send_telegram(text):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    body = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status == 200


# ---------------------------------------------------------------- report
def build_report(items, new_keys, errors, today):
    L = [f"# 부상 뉴스 & 재활 콘텐츠 초안 — {today.strftime('%Y-%m-%d %H:%M')} (KST)", "",
         "> 자동 생성. 뉴스는 출처 링크로만 참조. 재활 단계·운동은 일반적인 진행 예시이며 **게시 전 원우 님 검토 필수**. 의료 조언 아님.", ""]
    if not items:
        L.append("최근 48시간 내 수집된 축구 부상 뉴스가 없습니다.")
    else:
        L += ["## 요약", "", "| 신규 | 리그 | 선수 · 클럽 | 부위 | 정도 | 헤드라인 | 추출 |", "|---|---|---|---|---|---|---|"]
        for i in items:
            new = "🆕" if i["key"] in new_keys else ""
            who = " · ".join(x for x in [i.get("player"), i.get("club")] if x) or "-"
            part = i["rehab"]["part_ko"] if i["rehab"] else "-"
            sev = SEVERITY_KO[i["severity"]] + (f" · \"{i['duration_phrase']}\"" if i.get("duration_phrase") else "")
            L.append(f"| {new} | {i['league']} | {who} | {part} | {sev} | [{i['title']}]({i['link']}) ({i['source']}) | {i['extractor']} |")
        L.append("")
    cands = [i for i in items if i["rehab"] and i.get("player") and i["rehab"]["content_fit"] > 0]
    # Which injuries make the best @alpha_football_rehab reels: channel fit first, then severity, then novelty
    cands.sort(key=lambda i: (-i["rehab"]["content_fit"], {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3}[i["severity"]],
                              i["key"] not in new_keys))
    seen_players = set()
    cands = [i for i in cands if not (player_key(i["player"]) in seen_players or seen_players.add(player_key(i["player"])))]
    if cands:
        L += ["## 오늘의 콘텐츠 후보 (채널 적합도 순)", "",
              "| 순위 | 선수 | 부위 | 적합도 | 이유 |", "|---|---|---|---|---|"]
        for n, i in enumerate(cands[:5], 1):
            r = i["rehab"]
            L.append(f"| {n} | {i['player']} | {r['part_ko']} | {'★' * r['content_fit']} | {r['content_fit_why']} |")
        L.append("")
    for n, i in enumerate(cands[:5], 1):
        r = i["rehab"]
        who = " · ".join(x for x in [i.get("player"), i.get("club")] if x) or i["title"]
        L += [f"### {n}. {who} — {r['part_ko']} ({SEVERITY_KO[i['severity']]})",
              f"- [{i['title']}]({i['link']}) · {i['league']} · {i['source']}",
              f"- 콘텐츠 각도: {r['content_angle']}", f"- 주의: {r['red_flags']}", ""]
        a = r.get("anatomy") or {}
        if a:
            L += ["**어디·무슨 근육**", f"- 위치: {a.get('location', '')}", f"- 근육: {a.get('muscles', '')}",
                  f"- 집중: {a.get('focus', '')}", ""]
        L += [f"**촬영할 단계:** {r['phase']}" + (f" — {r['phase_goal']}" if r.get("phase_goal") else "")]
        L += [f"{k}. {d['name']}" + (f" — [영상]({d['video']})" if d["video"] else " — 영상 촬영 필요")
              for k, d in enumerate(r["drills"], 1)]
        L += ["", "<details><summary>전체 3단계</summary>", ""]
        L += [f"- **{p['name']}** — {p.get('goal', '')}: " + " · ".join(p["drills"]) for p in r["all_phases"]]
        L += ["", "</details>", "", "**캡션 (EN)**", "```", r["caption_en"], "```", "**캡션 (ES)**", "```", r["caption_es"], "```", ""]
    unconfirmed = [i for i in items if not i.get("player")]
    if unconfirmed:
        L += ["## 선수 미확인 (알림 보내지 않음)", ""]
        L += [f"- {i['league']}: [{i['title']}]({i['link']}) ({i['source']})" for i in unconfirmed] + [""]
    if errors:
        L += ["## 수집 오류", ""] + [f"- {e}" for e in errors] + [""]
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    for clubs in src["clubs"].values():
        for c in clubs:
            PLAYER_STOP.update(w.lower().strip(".") for w in c.split())
    for m in src.get("managers", []):
        PLAYER_STOP.update(w.lower() for w in m.split())
    lib = json.loads((HERE / "rehab_library.json").read_text(encoding="utf-8")); lib.pop("_note", None)
    videos = json.loads((HERE / "videos.json").read_text(encoding="utf-8")); videos.pop("_note", None)
    out_dir = Path(args.out) if args.out else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / "state.json"
    state = load_state(state_path)
    for rec in state["seen"].values():
        f = rec.get("facts") or {}
        if f.get("player") and all(t.lower() in PLAYER_STOP or t.lower() in COMMON_WORDS for t in f["player"].split()):
            f["player"] = None  # re-extract next time

    items, errors = collect(src, HERE / "sample_feed.xml" if args.sample else None)
    # Only unseen headlines go to the extractor (saves API cost); seen ones reuse stored facts
    fresh, cached = [], []
    for i in items:
        prev = state["seen"].get("title:" + i["title_key"])
        if prev and prev.get("facts") and prev["facts"].get("player"):
            i.update(prev["facts"]); cached.append(i)
        else:
            fresh.append(i)
    if src.get("fetch_article_body"):
        for i in fresh[:30]:
            i["body"] = fetch_article_body(i["link"], src.get("article_max_chars", 1500))
    extracted = extract(fresh) + cached
    extracted.sort(key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    now_iso = datetime.now(timezone.utc).isoformat()
    per_league, final, new_keys = {}, [], []
    for i in extracted:
        i["key"] = entity_key(i)
        i["rehab"] = rehab_block(i, lib, videos)
        n = per_league.get(i["league"], 0)
        if n >= src["max_per_league"]:
            continue
        per_league[i["league"]] = n + 1
        final.append(i)
        if i["key"] not in state["seen"]:
            new_keys.append(i["key"])
            if i["key"].startswith("title:") is False:
                state["seen"][i["key"]] = {"first_seen": now_iso, "title": i["title"]}
        facts = {k: i.get(k) for k in ("player", "club", "league", "body_part", "severity", "duration_weeks",
                                        "duration_phrase", "summary_en", "extractor")}
        state["seen"].setdefault("title:" + i["title_key"], {"first_seen": now_iso, "facts": facts})

    # Alerts: new items with a confirmed player only, one per player (best-sourced article wins)
    def alert_score(i):
        srcname = (i.get("source") or "").lower()
        rank = max((v for k, v in src.get("source_rank", {}).items() if k in srcname), default=1)
        return ((i["body_part"] != "unknown") * 10 + (i.get("duration_weeks") is not None) * 5
                + (i.get("extractor") == "claude") * 3 + rank + (1 if i.get("summary_en") else 0))

    by_player, fullest = {}, {}
    for i in final:
        if i["key"] in new_keys and i.get("player"):
            pk = player_key(i["player"])
            if pk not in by_player or alert_score(i) > alert_score(by_player[pk]):
                by_player[pk] = i
            if len(i["player"]) > len(fullest.get(pk, "")):
                fullest[pk] = i["player"]  # show the fullest name any article used
    for pk, i in by_player.items():
        i["player"] = fullest[pk]
    alerts = list(by_player.values())
    # First run with a chat id configured: say hello and send the 3 most relevant current items as a sample
    if os.environ.get("TELEGRAM_CHAT_ID") and not state.get("alerts_started") and not args.no_notify:
        try:
            send_telegram("✅ <b>AlphaBot 부상 알림 시작</b>\n30분마다 5대 리그 부상 뉴스를 확인하고, 새 소식만 보냅니다. "
                          "아래는 지금 수집된 소식 중 샘플 3건입니다.")
            state["alerts_started"] = datetime.now(timezone.utc).isoformat()
            sample = [i for i in final if i["rehab"] and i.get("player") and i["key"] not in new_keys]
            sample.sort(key=lambda i: {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3}[i["severity"]])
            alerts = sample[:3] + alerts
        except Exception as e:
            errors.append(f"Telegram hello: {e}")
    alerts.sort(key=lambda i: {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3}[i["severity"]])
    sent = 0
    if not args.no_notify:
        try:
            discover_telegram_chats()
        except Exception as e:
            errors.append(f"Telegram setup: {e}")
        cap = src["max_new_alerts_per_run"]
        if src.get("overflow_when_more_new") and len(alerts) > cap:
            cap = len(alerts)  # a busy 3-hour window: send them all rather than drop real news
        for i in alerts[:cap]:
            try:
                if send_telegram(telegram_message(i)):
                    sent += 1
            except Exception as e:
                errors.append(f"Telegram: {e}")

    today = datetime.now(KST)
    report = build_report(final, set(new_keys), errors, today)
    (out_dir / f"{today.strftime('%Y-%m-%d')}.md").write_text(report, encoding="utf-8")
    (out_dir / "latest.md").write_text(report, encoding="utf-8")
    serial = [{k: v for k, v in i.items() if k != "rehab"} | {"published": i["published"].isoformat() if i["published"] else None,
               "rehab_phase": i["rehab"]["phase"] if i["rehab"] else None} for i in final]
    (out_dir / "latest.json").write_text(json.dumps(serial, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    save_state(state_path, state)
    print(f"{len(items)} collected, {len(final)} football injuries, {len(new_keys)} new, "
          f"{sent} alerts sent, {len(errors)} errors -> {out_dir}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
