#!/usr/bin/env python3
"""Weekly Instagram data pull through the official Instagram Graph API.

What it collects (all official, no scraping):
  1. Our account  : followers, daily reach / new follows (28 days), last 30 posts with per-post insights
                    (views, reach, saves, shares, likes, comments) -> which of OUR reels work
  2. Benchmarks   : for each handle in tools/content_planner/benchmarks.json, public business-discovery data:
                    followers, media count, last 25 posts (likes, comments, caption, type, permalink) -> what works for THEM
  3. Learning     : posts are tagged with a content pattern (S&C / Rehab pattern ids) by keyword rules, and
                    pattern weights in benchmarks.json are refreshed from engagement (median likes+comments / account average)

Secrets (GitHub → Settings → Secrets → Actions):
  IG_ACCESS_TOKEN  long-lived token (Facebook Login path) or System User token (never expires, recommended)
  IG_USER_ID       our Instagram professional account id (numeric, from /me/accounts → instagram_business_account)
Optional: IG_GRAPH_HOST (default graph.facebook.com), IG_API_VERSION (default v21.0)

Output: docs/insights/ig/YYYY-MM-DD.json, docs/insights/ig/latest.md (+ benchmarks.json updated in place)
Usage : python tools/ig_insights/fetch.py [--dry-run]
"""
import argparse
import json
import os
import re
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BENCH = ROOT / "tools" / "content_planner" / "benchmarks.json"
OUT_DIR = ROOT / "docs" / "insights" / "ig"
KST = timezone(timedelta(hours=9))

HOST = os.environ.get("IG_GRAPH_HOST", "graph.facebook.com")
VER = os.environ.get("IG_API_VERSION", "v21.0")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
USER_ID = os.environ.get("IG_USER_ID", "")

# Keyword rules that map a caption to one of our content patterns (same ids as benchmarks.json)
PATTERN_RULES = [
    ("injury_react", r"\b(injur|out for|ruled out|rehab after|return(?:ed|s)? from)\b.*\b(week|month|acl|hamstring|groin|ankle)"),
    ("myth_bust", r"\b(myth|stop stretching|you don'?t need|actually|truth|lie|wrong|debunk)\b"),
    ("three_drills", r"\b(\d|three|3|five|5)\s+(drills?|exercises?|moves?)\b"),
    ("before_after_test", r"\b(before|after|from .* to|improved|faster by|seconds?|cm|test(?:ed)?)\b"),
    ("stop_doing", r"\b(stop doing|stop|never|don'?t do|mistake)\b"),
    ("pro_breakdown", r"\b(mbapp|haaland|vinic|bellingham|salah|messi|ronaldo|yamal|musiala|why .* is (?:so )?fast|breakdown)\b"),
    ("pov_session", r"\b(pov|session with|training with|my (?:player|athlete)|day in the life)\b"),
    ("progression_ladder", r"\b(level \d|phase \d|progression|beginner to|stage \d)\b"),
    ("test_yourself", r"\b(can you|test yourself|try this|challenge|how many)\b"),
    ("anatomy_explainer", r"\b(anatomy|muscle|tendon|ligament|where .* (?:tear|hurt)|why it hurts)\b"),
    ("physio_reacts", r"\b(reacts?|reaction|worst advice|physio (?:explains|reviews))\b"),
    ("explosive_visual", r"\b(plyo|jump|bound|sled|explosive|power)\b"),
]


def api(path, **params):
    params["access_token"] = TOKEN
    url = f"https://{HOST}/{VER}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "alpha-performance-insights"}), timeout=30) as r:
        return json.loads(r.read())


def safe(fn, *a, **k):
    try:
        return fn(*a, **k), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read()).get("error", {})
        except Exception:
            body = {"message": str(e)}
        return None, f"{body.get('message')} (code {body.get('code')})"
    except Exception as e:
        return None, str(e)


def classify(caption):
    t = (caption or "").lower()
    for pid, pat in PATTERN_RULES:
        if re.search(pat, t):
            return pid
    return "other"


def our_account():
    out, err = safe(api, USER_ID, fields="username,followers_count,media_count,follows_count")
    if err:
        return {"error": err}
    since = int((datetime.now(timezone.utc) - timedelta(days=28)).timestamp())
    daily, derr = safe(api, f"{USER_ID}/insights", metric="reach,follower_count", period="day", since=since)
    media, merr = safe(api, f"{USER_ID}/media", fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count", limit=30)
    posts = []
    for m in (media or {}).get("data", []):
        metrics = "views,reach,saved,shares,likes,comments" if m.get("media_product_type") == "REELS" else "reach,saved,shares,likes,comments"
        ins, ierr = safe(api, f"{m['id']}/insights", metric=metrics)
        if ierr and "views" in metrics:  # older accounts/API versions still call it plays
            ins, ierr = safe(api, f"{m['id']}/insights", metric=metrics.replace("views", "plays"))
        vals = {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value")) for d in (ins or {}).get("data", [])}
        posts.append({**{k: m.get(k) for k in ("id", "caption", "media_type", "media_product_type", "timestamp", "permalink", "like_count", "comments_count")},
                      "insights": vals, "pattern": classify(m.get("caption")), "insights_error": ierr})
    return {"profile": out, "daily": (daily or {}).get("data", []), "daily_error": derr, "posts": posts, "media_error": merr}


def benchmark(handle):
    fields = ("business_discovery.username(%s){username,name,followers_count,media_count,biography,"
              "media.limit(25){id,media_type,media_product_type,like_count,comments_count,caption,permalink,timestamp}}" % handle)
    data, err = safe(api, USER_ID, fields=fields)
    if err:
        return {"handle": handle, "error": err}
    bd = data.get("business_discovery", {})
    posts = [{**p, "pattern": classify(p.get("caption"))} for p in bd.get("media", {}).get("data", [])]
    return {"handle": handle, "followers": bd.get("followers_count"), "media_count": bd.get("media_count"), "name": bd.get("name"), "posts": posts}


def refresh_weights(bm, bench_results):
    """weight = 1..5 from engagement ratio of each pattern across benchmark accounts (median of (likes+comments)/account mean)."""
    ratios = {}
    for acc in bench_results:
        posts = acc.get("posts") or []
        eng = [(p.get("like_count") or 0) + (p.get("comments_count") or 0) for p in posts]
        if len(eng) < 5 or not statistics.mean(eng):
            continue
        avg = statistics.mean(eng)
        for p, e in zip(posts, eng):
            ratios.setdefault(p["pattern"], []).append(e / avg)
    evidence = {k: round(statistics.median(v), 2) for k, v in ratios.items() if len(v) >= 3}
    if not evidence:
        return {}
    for cat in bm["patterns"].values():
        for pat in cat:
            r = evidence.get(pat["id"])
            if r is not None:
                pat["weight_data"] = r
                pat["weight"] = max(1, min(5, round(1 + 4 * min(r, 2.0) / 2.0)))  # ratio 0→1, 1→3, 2+→5
                pat["samples"] = len(ratios[pat["id"]])
    return evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="no API calls; just show which handles would be fetched")
    args = ap.parse_args()
    bm = json.loads(BENCH.read_text(encoding="utf-8"))
    handles = [a["handle"] for lst in bm["accounts"].values() for a in lst]
    if args.dry_run or not TOKEN or not USER_ID:
        print(("dry run" if args.dry_run else "IG_ACCESS_TOKEN / IG_USER_ID not set") + f"; would fetch our account + {len(handles)} benchmarks: {handles}")
        return 0

    today = datetime.now(KST)
    ours = our_account()
    bench = [benchmark(h) for h in handles]

    # write follower counts and recent posts back into benchmarks.json
    for lst in bm["accounts"].values():
        for a in lst:
            r = next((b for b in bench if b["handle"] == a["handle"]), None)
            if r and not r.get("error"):
                a["followers"] = r["followers"]; a["name"] = r.get("name") or a.get("name"); a["note"] = a.get("note", "").replace("확인 필요", "").strip()
                top = sorted(r["posts"], key=lambda p: (p.get("like_count") or 0) + (p.get("comments_count") or 0), reverse=True)[:5]
                a["top_reels"] = [{"title": (p.get("caption") or "")[:80], "likes": p.get("like_count"), "comments": p.get("comments_count"),
                                   "pattern": p["pattern"], "url": p.get("permalink"), "date": (p.get("timestamp") or "")[:10]} for p in top]
                a["fetched"] = today.strftime("%Y-%m-%d")
    evidence = refresh_weights(bm, bench)
    BENCH.write_text(json.dumps(bm, ensure_ascii=False, indent=2), encoding="utf-8")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{today.strftime('%Y-%m-%d')}.json").write_text(json.dumps({"ours": ours, "benchmarks": bench, "pattern_evidence": evidence}, ensure_ascii=False, indent=1), encoding="utf-8")

    L = [f"# 인스타 데이터 — {today.strftime('%Y-%m-%d')}", ""]
    prof = ours.get("profile") or {}
    if prof:
        L += [f"## 우리 계정 @{prof.get('username')}", f"- 팔로워 {prof.get('followers_count'):,} · 게시물 {prof.get('media_count')}", ""]
        posts = [p for p in ours["posts"] if not p.get("insights_error")]
        posts.sort(key=lambda p: (p["insights"].get("views") or p["insights"].get("plays") or p["insights"].get("reach") or 0), reverse=True)
        L += ["| 날짜 | 패턴 | 조회/도달 | 저장 | 공유 | 좋아요 | 캡션 |", "|---|---|---|---|---|---|---|"]
        for p in posts[:15]:
            i = p["insights"]
            L.append(f"| {(p.get('timestamp') or '')[:10]} | {p['pattern']} | {i.get('views') or i.get('plays') or i.get('reach') or '-'} | {i.get('saved', '-')} | {i.get('shares', '-')} | {i.get('likes', p.get('like_count'))} | [{(p.get('caption') or '')[:50]}]({p.get('permalink')}) |")
        L.append("")
        by_pat = {}
        for p in posts:
            v = p["insights"].get("views") or p["insights"].get("plays") or p["insights"].get("reach") or 0
            by_pat.setdefault(p["pattern"], []).append(v)
        if by_pat:
            L += ["**우리 계정 패턴별 중앙값 조회**", ""] + [f"- {k}: {int(statistics.median(v)):,} ({len(v)}개)" for k, v in sorted(by_pat.items(), key=lambda kv: -statistics.median(kv[1]))] + [""]
    else:
        L += [f"## 우리 계정: 오류 — {ours.get('error')}", ""]
    L += ["## 벤치마크", "", "| 계정 | 팔로워 | 최근 25개 평균 (좋아요+댓글) | 가장 센 패턴 |", "|---|---|---|---|"]
    for b in bench:
        if b.get("error"):
            L.append(f"| @{b['handle']} | 오류 | {b['error']} | |"); continue
        eng = [(p.get("like_count") or 0) + (p.get("comments_count") or 0) for p in b["posts"]]
        pats = {}
        for p, e in zip(b["posts"], eng):
            pats.setdefault(p["pattern"], []).append(e)
        best = max(pats.items(), key=lambda kv: statistics.median(kv[1]))[0] if pats else "-"
        L.append(f"| @{b['handle']} | {b['followers']:,} | {int(statistics.mean(eng)) if eng else '-'} | {best} |")
    if evidence:
        L += ["", "**패턴 가중치 근거 (참여율 비, 1.0 = 계정 평균)**", ""] + [f"- {k}: {v}" for k, v in sorted(evidence.items(), key=lambda kv: -kv[1])]
    (OUT_DIR / "latest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    errs = [b["handle"] for b in bench if b.get("error")]
    print(f"ours: {'ok' if prof else ours.get('error')} | benchmarks ok: {len(bench) - len(errs)}/{len(bench)} | errors: {errs} | weights updated: {list(evidence)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
