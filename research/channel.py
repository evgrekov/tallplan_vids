"""Channel summary from saved Bright Data files: python3 research/channel.py <handle> [top=8]"""
import json, pathlib, statistics, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
h, top = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8
d = ROOT / "stats/refs" / h
prof = json.loads(sorted(d.glob("*_profile.json"))[-1].read_text())
prof = prof[0] if prof else {}
posts = [p for p in json.loads(sorted(d.glob("*_posts.json"))[-1].read_text()) if p.get("play_count") is not None]
n = lambda p, k: int(p.get(k) or 0)  # Bright Data returns some counts as strings
v = [p["play_count"] for p in posts]
med = statistics.median(v) if v else 0
dates = sorted(p["create_time"][:10] for p in posts)
print(f"📊 @{h}: followers {prof.get('followers')}, videos {prof.get('videos_count')}, likes {prof.get('likes')}, created {prof.get('create_time', '')[:10]}")
print(f"   posts {len(posts)} {dates[0] if dates else ''}..{dates[-1] if dates else ''}, median {med:.0f}, max {max(v) if v else 0}")
for p in sorted(posts, key=lambda p: -p["play_count"])[:top]:
    er = sum(n(p, k) for k in ("digg_count", "comment_count", "share_count", "collect_count")) / max(p["play_count"], 1)
    kind = p.get("post_type") or ("photo" if "/photo/" in p["url"] else "video")
    print(f"   {p['play_count']:>9} x{p['play_count'] / max(med, 1):>6.1f} ER {er:.1%} sv {n(p, 'collect_count') / max(p['play_count'], 1):.1%} {p['create_time'][:10]} {kind:5} {p.get('video_duration')}s {p['url'].split('/')[-1]} {(p.get('description') or '')[:60]!r}")
