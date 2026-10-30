#!/usr/bin/env python3
"""Injury watch: collect football injury news for the five big leagues,
classify body part and severity, and draft rehab content for the channel.

Runs daily in GitHub Actions (see .github/workflows/injury-watch.yml).
Output: docs/injuries/YYYY-MM-DD.md and docs/injuries/latest.json

Standard library only, so it runs anywhere without installing packages.
Usage:
  python tools/injury_watch/injury_watch.py            # live (Google News RSS)
  python tools/injury_watch/injury_watch.py --sample   # offline test with sample_feed.xml
"""
import argparse
import html
import json
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

# ---------- classification rules ----------
# Order matters: the first matching body part wins, so specific terms come first.
BODY_PART_RULES = [
    ("concussion", r"concussion|head injury|head knock|skull|facial fracture"),
    ("achilles", r"achilles"),
    ("hamstring", r"hamstring|back of (the|his) thigh"),
    ("knee_acl", r"\bacl\b|cruciate|meniscus|\bmcl\b|\blcl\b|\bpcl\b|patella"),
    ("groin", r"groin|adductor|hernia"),
    ("calf", r"\bcalf\b|soleus|gastrocnemius"),
    ("quad", r"quad|rectus femoris|\bthigh\b"),
    ("ankle", r"ankle|syndesmosis"),
    ("foot", r"metatarsal|\bfoot\b|\btoe\b|plantar|heel"),
    ("hip", r"\bhip\b|labrum|labral"),
    ("back", r"\bback injury\b|\bback problem\b|lumbar|spine|spinal|disc"),
    ("shoulder", r"shoulder|collarbone|clavicle|\barm\b|elbow|wrist"),
    ("knee_other", r"\bknee\b"),
    ("muscle_general", r"muscle|muscular"),
]

# Always severe, whatever the quoted timeline
HARD_SEVERE_WORDS = r"rupture|ruptured|fracture|fractured|broken|surgery|operation|rest of the season|season over|season-ending"
# Severe only when no timeline is given
SOFT_SEVERE_WORDS = r"torn|tear|long-term|months"
MINOR_WORDS = r"\bknock\b|minor|precaution|slight|doubt|fitness test|late fitness|assessed"
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
    "several": 3, "a few": 3, "couple of": 2, "a": 1,
}
DURATION_RE = re.compile(
    r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|several|a few|couple of|a)\s*(?:to|-|–)?\s*(\d+)?\s*(day|week|month)s?",
    re.I,
)
# Words that usually mean the headline is about an injury, not a return
INJURY_SIGNALS = r"injur|out for|ruled out|sidelined|miss|blow|setback|surgery|fracture|tear|strain|knock|limp|stretcher|withdraw|doubt"
NOT_INJURY = r"return|back in training|fit again|recovered|comeback|available again|injury-free|transfer|signs|loan|sack|appoint"


def classify_body_part(text):
    t = text.lower()
    for key, pattern in BODY_PART_RULES:
        if re.search(pattern, t):
            return key
    return None


def extract_duration_weeks(text):
    m = DURATION_RE.search(text)
    if not m:
        return None, None
    n1, n2, unit = m.group(1).lower(), m.group(2), m.group(3).lower()
    n = int(n1) if n1.isdigit() else NUMBER_WORDS.get(n1, 1)
    if n2:
        n = int(n2)  # "4-6 weeks" -> take the upper bound
    weeks = {"day": n / 7, "week": n, "month": n * 4.3}[unit]
    return round(weeks, 1), m.group(0)


def classify_severity(text, body_part):
    t = text.lower()
    weeks, phrase = extract_duration_weeks(t)
    if re.search(HARD_SEVERE_WORDS, t) or body_part in ("knee_acl", "achilles"):
        return "severe", weeks, phrase
    if weeks is not None:
        return ("minor" if weeks < 2 else "moderate" if weeks <= 8 else "severe"), weeks, phrase
    if re.search(SOFT_SEVERE_WORDS, t):
        return "severe", None, phrase
    if re.search(MINOR_WORDS, t):
        return "minor", None, phrase
    return "unknown", None, phrase


def looks_like_injury(text):
    t = text.lower()
    return bool(re.search(INJURY_SIGNALS, t)) and not re.search(NOT_INJURY, t)


# ---------- fetching ----------
def google_news_url(query, hours_back):
    days = max(1, round(hours_back / 24))
    q = f"{query} when:{days}d"
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "en", "gl": "US", "ceid": "US:en"}
    )


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (injury-watch)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_rss(xml_bytes, league):
    items = []
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        link = (it.findtext("link") or "").strip()
        pub = it.findtext("pubDate")
        source = it.findtext("source") or ""
        # Google News titles end with " - Source"
        if " - " in title and not source:
            title, source = title.rsplit(" - ", 1)
        elif " - " in title and title.endswith(source):
            title = title[: -(len(source) + 3)]
        try:
            when = parsedate_to_datetime(pub) if pub else None
        except Exception:
            when = None
        items.append({"league": league, "title": title.strip(), "link": link,
                      "source": source.strip(), "published": when})
    return items


def collect(config, sample_path=None):
    hours_back = config["hours_back"]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    all_items, errors = [], []
    for league, queries in config["leagues"].items():
        if sample_path:
            try:
                all_items += [i for i in parse_rss(Path(sample_path).read_bytes(), league)
                              if i["league"] == league or True]
            except Exception as e:
                errors.append(f"{league}: {e}")
            continue
        for q in queries:
            try:
                all_items += parse_rss(fetch(google_news_url(q, hours_back)), league)
            except Exception as e:
                errors.append(f"{league} / {q}: {e}")
    # Sample feed carries its own league in the title prefix "[League]"
    if sample_path:
        fixed = []
        for i in all_items:
            m = re.match(r"\[(.+?)\]\s*(.*)", i["title"])
            if m:
                i["league"], i["title"] = m.group(1), m.group(2)
            fixed.append(i)
        all_items = fixed
    # Drop old items, non-injury headlines and duplicates
    seen, kept = set(), []
    for i in all_items:
        if i["published"] and i["published"] < cutoff and not sample_path:
            continue
        if not looks_like_injury(i["title"]):
            continue
        key = re.sub(r"[^a-z0-9]", "", i["title"].lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        kept.append(i)
    # Cap per league
    per_league = {}
    out = []
    for i in sorted(kept, key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        n = per_league.get(i["league"], 0)
        if n >= config["max_per_league"]:
            continue
        per_league[i["league"]] = n + 1
        out.append(i)
    return out, errors


# ---------- content drafting ----------
SEVERITY_KO = {"minor": "경미 (2주 미만)", "moderate": "중간 (2~8주)", "severe": "중증 (8주 이상 / 수술 / 파열)", "unknown": "미상"}
SEVERITY_EN = {"minor": "minor", "moderate": "moderate", "severe": "serious", "unknown": "unconfirmed"}


def draft(item, lib):
    bp = item["body_part"]
    entry = lib.get(bp) if bp else None
    sev = item["severity"]
    if not entry:
        return None
    # Which phase to lead with: severe -> phase 1 (educational), minor -> phase 3
    lead = {"minor": 2, "moderate": 1, "severe": 0, "unknown": 1}[sev]
    phase = entry["phases"][lead]
    drills = phase["drills"]
    hook_en = f"Another {entry['en']} injury in the {item['league']}. Here's what the comeback looks like."
    caption_en = (
        f"{hook_en}\n\n"
        f"Most {entry['en']} rehab has 3 stages. This is the stage that gets rushed:\n"
        f"{phase['name']}\n"
        + "\n".join(f"{n}. {d}" for n, d in enumerate(drills, 1))
        + "\n\n⚠️ General training education, not medical advice. If you're injured, see a physio first."
        + "\n\n💬 Comment SPEED for my 6-week speed program (for healthy players)."
    )
    caption_es = (
        f"Otra lesión de {entry['es']} en {item['league']}. Así es la vuelta.\n\n"
        f"La rehabilitación de {entry['es']} tiene 3 fases. Esta es la que más se apresura:\n"
        + "\n".join(f"{n}. {d}" for n, d in enumerate(drills, 1))
        + "\n\n⚠️ Educación general, no consejo médico. Si estás lesionado, consulta a un fisio primero."
        + "\n\n💬 Comenta VELOCIDAD para mi programa de velocidad de 6 semanas (para jugadores sanos)."
    )
    return {
        "hook_en": hook_en,
        "phase_to_film": phase["name"],
        "drills_to_film": drills,
        "all_phases": entry["phases"],
        "content_angle": entry["content_angle"],
        "red_flags": entry["red_flags"],
        "caption_en": caption_en,
        "caption_es": caption_es,
    }


def build_report(items, errors, lib, today):
    lines = [f"# 부상 뉴스 & 재활 콘텐츠 초안 — {today.strftime('%Y-%m-%d')} (KST)", ""]
    lines.append("> 자동 생성. 뉴스 제목은 출처 링크로만 참조하고 본문은 복사하지 않음. "
                 "재활 단계와 운동은 일반적인 진행 예시이며, **게시 전 원우 님이 검토·수정**해야 함. 의료 조언 아님.")
    lines.append("")
    if not items:
        lines.append("최근 48시간 내 수집된 부상 뉴스가 없습니다.")
    # Summary table
    if items:
        lines += ["## 요약", "", "| 리그 | 헤드라인 | 부위 | 정도 | 출처 |", "|---|---|---|---|---|"]
        for i in items:
            bp = lib.get(i["body_part"], {}).get("ko", "-") if i["body_part"] else "-"
            sev = SEVERITY_KO[i["severity"]]
            if i["duration_phrase"]:
                sev += f" · \"{i['duration_phrase']}\""
            lines.append(f"| {i['league']} | [{i['title']}]({i['link']}) | {bp} | {sev} | {i['source'] or '-'} |")
        lines.append("")
    # Content drafts: pick the best candidates (classified body part, severity known first)
    drafts = [i for i in items if i["draft"]]
    drafts.sort(key=lambda i: ({"severe": 0, "moderate": 1, "minor": 2, "unknown": 3}[i["severity"]]))
    if drafts:
        lines += ["## 오늘의 콘텐츠 후보 (우선순위 순)", ""]
    for n, i in enumerate(drafts[:5], 1):
        d = i["draft"]
        bp = lib[i["body_part"]]
        lines += [
            f"### {n}. {i['title']}",
            f"- 리그: {i['league']} · 부위: **{bp['ko']}** · 정도: **{SEVERITY_KO[i['severity']]}** · [출처]({i['link']})",
            f"- 콘텐츠 각도: {d['content_angle']}",
            f"- 주의: {d['red_flags']}",
            "",
            f"**촬영할 단계:** {d['phase_to_film']}",
        ]
        lines += [f"{k}. {x}" for k, x in enumerate(d["drills_to_film"], 1)]
        lines += ["", "<details><summary>전체 3단계</summary>", ""]
        for ph in d["all_phases"]:
            lines.append(f"- **{ph['name']}**: " + " · ".join(ph["drills"]))
        lines += ["", "</details>", "", "**캡션 (EN)**", "```", d["caption_en"], "```",
                  "**캡션 (ES)**", "```", d["caption_es"], "```", ""]
    unclassified = [i for i in items if not i["body_part"]]
    if unclassified:
        lines += ["## 부위 미분류 (헤드라인만으로 판단 불가)", ""]
        lines += [f"- {i['league']}: [{i['title']}]({i['link']})" for i in unclassified]
        lines.append("")
    if errors:
        lines += ["## 수집 오류", ""] + [f"- {e}" for e in errors] + [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use sample_feed.xml instead of live news")
    ap.add_argument("--out", default=None, help="output directory (default docs/injuries)")
    args = ap.parse_args()

    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    lib = json.loads((HERE / "rehab_library.json").read_text(encoding="utf-8"))
    lib.pop("_note", None)

    items, errors = collect(config, sample_path=HERE / "sample_feed.xml" if args.sample else None)
    for i in items:
        i["body_part"] = classify_body_part(i["title"])
        i["severity"], i["duration_weeks"], i["duration_phrase"] = classify_severity(i["title"], i["body_part"])
        i["draft"] = draft(i, lib)

    today = datetime.now(KST)
    out_dir = Path(args.out) if args.out else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(items, errors, lib, today)
    (out_dir / f"{today.strftime('%Y-%m-%d')}.md").write_text(report, encoding="utf-8")
    (out_dir / "latest.md").write_text(report, encoding="utf-8")
    serial = [{**i, "published": i["published"].isoformat() if i["published"] else None} for i in items]
    (out_dir / "latest.json").write_text(json.dumps(serial, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(items)} injury items, {sum(1 for i in items if i['draft'])} drafts, {len(errors)} errors -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
