#!/usr/bin/env python3
"""Weekly reel planner for @alpha_football_rehab.

Every Monday (GitHub Actions) it drafts 3 reels for the week:
  Tue  slot 1  Rehab  · injury_react  — reacts to this week's best pro injury (from the injury watch)
  Thu  slot 2  S&C    · rotating pattern (pro_breakdown, three_drills, before_after_test, ...)
  Fri  slot 3  Rehab  · rotating pattern (myth_bust, anatomy_explainer, progression_ladder, ...)

Inputs : tools/content_planner/benchmarks.json   (accounts, patterns, channel rules)
         tools/injury_watch/rehab_library.json   (anatomy, phases, drills)
         docs/injuries/latest.json               (current injury candidates with content_fit)
         docs/content/weekly/history.json        (what was planned before, to avoid repeats)
Output : docs/content/weekly/YYYY-Www.md  +  Telegram summary (same bot/group as the injury alerts)

With ANTHROPIC_API_KEY the scripts, shot lists and captions are written by Claude (structured output);
without it a template version is produced so the week never goes without a plan.

Usage: python tools/content_planner/planner.py [--no-notify] [--out DIR]
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools" / "injury_watch"))
import injury_watch as iw  # noqa: E402  (send_telegram, player_key, KST)

OUT_DIR = ROOT / "docs" / "content" / "weekly"
SEV_KO = {"minor": "경미", "moderate": "중간", "severe": "중증", "unknown": "미상"}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "reels": {
            "type": "array",
            "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "slot": {"type": "integer"},
                    "title_ko": {"type": "string", "description": "내부용 제목, 한국어"},
                    "hook_en": {"type": "string", "description": "first 2 seconds on-screen hook, max 12 words"},
                    "hook_de": {"type": "string"},
                    "hook_es": {"type": "string"},
                    "why_it_works_ko": {"type": "string", "description": "어떤 벤치마크 패턴과 채널 데이터 근거인지 2문장"},
                    "beats": {
                        "type": "array", "minItems": 4, "maxItems": 6,
                        "items": {"type": "object",
                                  "properties": {"seconds": {"type": "string"}, "action_ko": {"type": "string", "description": "원우 님이 화면에서 하는 것"},
                                                 "voiceover_ko": {"type": "string", "description": "원우 님이 말할 한국어 대사 (더빙/번역 원문)"},
                                                 "on_screen_en": {"type": "string"}},
                                  "required": ["seconds", "action_ko", "voiceover_ko", "on_screen_en"], "additionalProperties": False}
                    },
                    "drills": {"type": "array", "minItems": 0, "maxItems": 3,
                               "items": {"type": "object", "properties": {"name_en": {"type": "string"}, "dose": {"type": "string"}, "cue_ko": {"type": "string"}},
                                         "required": ["name_en", "dose", "cue_ko"], "additionalProperties": False}},
                    "shot_list_ko": {"type": "array", "items": {"type": "string"}, "description": "촬영 장소·앵글·소품 3~5줄"},
                    "caption_en": {"type": "string"}, "caption_de": {"type": "string"}, "caption_es": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                    "risk_ko": {"type": "string", "description": "저작권·초상권·의료 표현 주의점, 없으면 '없음'"}
                },
                "required": ["slot", "title_ko", "hook_en", "hook_de", "hook_es", "why_it_works_ko", "beats", "drills",
                             "shot_list_ko", "caption_en", "caption_de", "caption_es", "hashtags", "risk_ko"],
                "additionalProperties": False
            }
        }
    },
    "required": ["reels"], "additionalProperties": False
}

SYSTEM = (
    "You plan short-form Instagram reels for @alpha_football_rehab, run by Coach Wonwoo: Korean, ex-UDT, rehab-trained football "
    "speed & return-to-play coach living in Dortmund, coaching a Korea U-20 international. He films himself demonstrating; "
    "no match footage, no player photos, no medical claims. Audience: men 25-44, Spanish > English > Arabic > Portuguese > German. "
    "Every reel sells nothing directly but ends with the comment keyword CTA. Write voiceover in natural spoken Korean (반말 아님, 편한 존댓말), "
    "hooks in punchy English/German/Spanish. Keep drills real and conservative; prefer the drills given in the rehab library."
)


def load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def week_id(now):
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


def pick_injury(items, lib, history):
    used = {h.get("player_key") for h in history}
    cands = []
    for i in items:
        if not i.get("player") or i.get("body_part") in (None, "unknown"):
            continue
        entry = lib.get(i["body_part"])
        if not entry or entry.get("content_fit", 0) < 3:
            continue
        if iw.player_key(i["player"]) in used:
            continue
        cands.append(i)
    cands.sort(key=lambda i: (-lib[i["body_part"]]["content_fit"], {"severe": 0, "moderate": 1, "minor": 2, "unknown": 3}[i["severity"]],
                              i.get("published") or ""), )
    cands.sort(key=lambda i: -lib[i["body_part"]]["content_fit"])  # stable: fit first, then severity, then recency
    return cands[0] if cands else None


def rotate(patterns, history, category, exclude=()):
    recent = [h.get("pattern") for h in history[-9:]]
    pool = [p for p in patterns[category] if p["id"] not in exclude]
    pool.sort(key=lambda p: (p["id"] in recent, -p["weight"]))
    return pool[0]


def build_brief(now, injury, lib, pat_sc, pat_rehab, bm):
    ch = bm["channel"]
    lines = [f"Week {week_id(now)}. Posting Tue/Thu/Fri 21:00 KST. CTA keywords: {ch['posting']['cta_keyword']} (EN), {ch['posting']['cta_keyword_es']} (ES).",
             f"Pillars: {', '.join(ch['pillars'])}. Differentiators: {', '.join(ch['differentiators'])}.",
             f"Proof: demo reels gained followers {ch['proof_from_insights']['demo_reels_follow_gain']}, star-player clips only {ch['proof_from_insights']['star_content_follow_gain']}.",
             "Rules: " + " / ".join(ch["rules"]), ""]
    if injury:
        e = lib[injury["body_part"]]
        lines += [f"SLOT 1 (Tue, Rehab · injury_react): {injury['player']} ({injury.get('club') or '?'}, {injury['league']}) — {e['en']} injury, "
                  f"severity {injury['severity']}, duration {injury.get('duration_phrase') or injury.get('duration_weeks') or 'unknown'}. Source headline: {injury['title']}.",
                  f"  Anatomy (ko): {e['anatomy']['location']} / {e['anatomy']['muscles']} / focus: {e['anatomy']['focus']}",
                  "  Phases: " + " | ".join(f"{p['name']}: {', '.join(p['drills'])}" for p in e["phases"]), ""]
    else:
        lines += ["SLOT 1 (Tue, Rehab · injury_react): no fresh pro injury this week — do an evergreen 'most common injury this month' reel on hamstrings.", ""]
    lines += [f"SLOT 2 (Thu, S&C · {pat_sc['id']}): pattern '{pat_sc['name']}', example hook: {pat_sc['hook_en']}. Why: {pat_sc['why']}",
              f"SLOT 3 (Fri, Rehab · {pat_rehab['id']}): pattern '{pat_rehab['name']}', example hook: {pat_rehab['hook_en']}. Why: {pat_rehab['why']}", "",
              "Rehab library body parts available (use their drills): " + ", ".join(f"{k}={v['en']}" for k, v in lib.items()),
              "Benchmark accounts: " + "; ".join(f"@{a['handle']} ({cat}, {a['followers'] or '?'} followers)" for cat, lst in bm["accounts"].items() for a in lst)]
    return "\n".join(lines)


def plan_with_claude(brief):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic()
    try:
        r = client.beta.messages.create(
            model=os.environ.get("INJURY_WATCH_MODEL") or "claude-opus-5-5",
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": PLAN_SCHEMA}},
            messages=[{"role": "user", "content": "Plan this week's 3 reels.\n\n" + brief}],
        )
    except anthropic.APIStatusError as e:
        print(f"Claude API error {e.status_code}: {e.message}", file=sys.stderr); return None
    except anthropic.APIConnectionError as e:
        print(f"Claude connection error: {e}", file=sys.stderr); return None
    if r.stop_reason == "refusal":
        print("Claude declined", file=sys.stderr); return None
    text = next((b.text for b in r.content if b.type == "text"), "")
    try:
        return json.loads(text)["reels"]
    except Exception:
        print("Claude returned non-JSON", file=sys.stderr); return None


def plan_template(injury, lib, pat_sc, pat_rehab):
    """No API key: a usable skeleton the coach fills in."""
    def reel(slot, title, hook, pattern_why, drills, part):
        return {"slot": slot, "title_ko": title, "hook_en": hook, "hook_de": hook, "hook_es": hook,
                "why_it_works_ko": pattern_why,
                "beats": [{"seconds": "0-2", "action_ko": "카메라 정면, 훅 한 문장", "voiceover_ko": "(훅)", "on_screen_en": hook},
                          {"seconds": "2-8", "action_ko": "부위를 손으로 짚으며 설명", "voiceover_ko": "(어디·무슨 근육)", "on_screen_en": part},
                          {"seconds": "8-25", "action_ko": "운동 3개 시연, 각 5초", "voiceover_ko": "(세트·횟수·큐)", "on_screen_en": "1 / 2 / 3"},
                          {"seconds": "25-30", "action_ko": "정면, CTA", "voiceover_ko": "댓글에 SPEED라고 남겨 주세요", "on_screen_en": "Comment SPEED"}],
                "drills": [{"name_en": d, "dose": "3×8", "cue_ko": ""} for d in drills[:3]],
                "shot_list_ko": ["잔디 또는 공원, 자연광", "정면 1 + 측면 1 앵글", "콘·밴드 등 소품"],
                "caption_en": hook + "\n\n⚠️ General education, not medical advice.\n💬 Comment SPEED for the 6-week program.",
                "caption_de": hook, "caption_es": hook, "hashtags": ["#footballtraining", "#speedtraining", "#rehab"], "risk_ko": "없음"}
    out = []
    if injury:
        e = lib[injury["body_part"]]
        out.append(reel(1, f"{injury['player']} {e['ko']} 부상 반응", f"{injury['player']} is out. Here's what rehab actually looks like",
                        "부상 뉴스 반응 = 시의성 + 전문성", e["phases"][1]["drills"], e["en"]))
    else:
        e = lib["hamstring"]
        out.append(reel(1, "이달의 부상: 햄스트링", "The most common injury in football, explained", "evergreen", e["phases"][1]["drills"], e["en"]))
    out.append(reel(2, f"S&C · {pat_sc['name']}", pat_sc["hook_en"], pat_sc["why"], ["A-skips", "Wall drill acceleration", "Sprint build-ups 60→90%"], "Speed"))
    out.append(reel(3, f"Rehab · {pat_rehab['name']}", pat_rehab["hook_en"], pat_rehab["why"], lib["ankle"]["phases"][1]["drills"], lib["ankle"]["en"]))
    return out


def render_md(now, reels, injury, pat_sc, pat_rehab, by_claude):
    wk = week_id(now)
    L = [f"# 주간 릴스 기획 — {wk} ({now.strftime('%Y-%m-%d')} 생성)", "",
         f"> {'Claude가 작성한 초안' if by_claude else '템플릿 초안(API 키 없음)'}. 게시 전 원우 님이 대사·운동을 검토. 선수 영상·사진 사용 금지, 의료 조언 아님 문구 유지.", "",
         "| 요일 | 슬롯 | 패턴 | 제목 |", "|---|---|---|---|"]
    days = ["화", "목", "금"]
    pats = ["injury_react" if injury else "evergreen", pat_sc["id"], pat_rehab["id"]]
    for r, d, p in zip(reels, days, pats):
        L.append(f"| {d} | {r['slot']} | {p} | {r['title_ko']} |")
    L.append("")
    for r, d in zip(reels, days):
        L += [f"## {d} · {r['title_ko']}", f"- 훅 EN: **{r['hook_en']}**", f"- 훅 DE: {r['hook_de']}", f"- 훅 ES: {r['hook_es']}",
              f"- 왜 통하나: {r['why_it_works_ko']}", f"- 주의: {r['risk_ko']}", "", "**구성 (초 단위)**",
              "| 초 | 화면에서 하는 것 | 한국어 대사 | 화면 자막 (EN) |", "|---|---|---|---|"]
        L += [f"| {b['seconds']} | {b['action_ko']} | {b['voiceover_ko']} | {b['on_screen_en']} |" for b in r["beats"]]
        if r["drills"]:
            L += ["", "**운동**"] + [f"{n}. {x['name_en']} — {x['dose']} · {x['cue_ko']}" for n, x in enumerate(r["drills"], 1)]
        L += ["", "**촬영 메모**"] + [f"- {s}" for s in r["shot_list_ko"]]
        L += ["", "**캡션 EN**", "```", r["caption_en"], "```", "**캡션 DE**", "```", r["caption_de"], "```", "**캡션 ES**", "```", r["caption_es"], "```",
              "해시태그: " + " ".join(r["hashtags"]), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-notify", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    now = datetime.now(iw.KST)
    out_dir = Path(args.out) if args.out else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    bm = load_json(HERE / "benchmarks.json", {})
    lib = load_json(ROOT / "tools" / "injury_watch" / "rehab_library.json", {}); lib.pop("_note", None)
    items = load_json(ROOT / "docs" / "injuries" / "latest.json", [])
    history = load_json(out_dir / "history.json", [])

    injury = pick_injury(items, lib, history)
    pat_sc = rotate(bm["patterns"], history, "S&C")
    pat_rehab = rotate(bm["patterns"], history, "Rehab", exclude=("injury_react",))
    brief = build_brief(now, injury, lib, pat_sc, pat_rehab, bm)

    reels = plan_with_claude(brief)
    by_claude = reels is not None
    if not reels:
        reels = plan_template(injury, lib, pat_sc, pat_rehab)

    wk = week_id(now)
    md = render_md(now, reels, injury, pat_sc, pat_rehab, by_claude)
    (out_dir / f"{wk}.md").write_text(md, encoding="utf-8")
    (out_dir / "latest.md").write_text(md, encoding="utf-8")
    history.append({"week": wk, "pattern": pat_sc["id"], "player_key": iw.player_key(injury["player"]) if injury else None,
                    "titles": [r["title_ko"] for r in reels]})
    history.append({"week": wk, "pattern": pat_rehab["id"]})
    (out_dir / "history.json").write_text(json.dumps(history[-60:], ensure_ascii=False, indent=1), encoding="utf-8")

    if not args.no_notify:
        link = f"https://github.com/jjoshkr/alphaperformance/blob/claude/practical-cray-ezhcif/docs/content/weekly/{wk}.md"
        days = ["화", "목", "금"]
        msg = [f"🎬 <b>이번 주 릴스 기획 {wk}</b> ({'Claude 초안' if by_claude else '템플릿'})", ""]
        for r, d in zip(reels, days):
            msg += [f"<b>{d} · {iw.tg_escape(r['title_ko'])}</b>", f"훅: {iw.tg_escape(r['hook_en'])}",
                    f"운동: {iw.tg_escape(' · '.join(x['name_en'] for x in r['drills']) or '-')}", ""]
        msg.append("<i>전체 대사·촬영 메모·EN/DE/ES 캡션은 버튼으로</i>")
        iw.send_telegram("\n".join(msg), buttons=[("📄 전체 기획 보기", link)])
    print(f"{wk}: {'claude' if by_claude else 'template'} plan, injury={injury['player'] if injury else None}, "
          f"patterns={pat_sc['id']}/{pat_rehab['id']} -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
