"""Reference TikTok research: Bright Data scrapes + local video analysis (no paid AI).
Usage:
  python3 research/ref.py posts <handle> [n=60]      channel posts  → stats/refs/<handle>/<date>_posts.json
  python3 research/ref.py profile <handle>           channel profile → stats/refs/<handle>/<date>_profile.json
  python3 research/ref.py comments <video_url>       comments → stats/refs/<handle>/<date>_comments_<id>.json
  python3 research/ref.py video <video_url>          download to Drive, frames + cuts + speech + audio → research/work/<handle>/<id>/
  python3 research/ref.py photo <post_url>           photo carousel: slides + sound to Drive (needs saved posts)
"""
import datetime, json, pathlib, re, shutil, statistics, subprocess, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = re.search(r"BRIGHTDATA_API=(\S+)", (ROOT / ".env").read_text()).group(1)
DRIVE = pathlib.Path.home() / "Library/CloudStorage/GoogleDrive-evgrekov@gmail.com/My Drive/Projects/TT30/src/02_sources"
WHISPER = [str(pathlib.Path.home() / ".local/bin/mlx_whisper"), "--model", str(pathlib.Path.home() / ".cache/mlx-models/whisper-small")]
DS = {"profile": "gd_l1villgoiiidt09ci", "posts": "gd_lu702nij2f790tmv9h", "comments": "gd_lkf2st302ap89utw5k"}
TODAY = datetime.date.today().isoformat()

def bd(path, body=None):
    req = urllib.request.Request("https://api.brightdata.com/datasets/v3/" + path, json.dumps(body).encode() if body else None,
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))

def scrape(kind, inputs, out, discover=False):
    q = f"trigger?dataset_id={DS[kind]}&include_errors=true" + ("&type=discover_new&discover_by=profile_url" if discover else "")
    sid = bd(q, inputs)["snapshot_id"]
    print(f"🛰️  {kind} snapshot {sid}", flush=True)
    while (st := bd(f"progress/{sid}")["status"]) not in ("ready", "failed"):
        time.sleep(15)
    data = bd(f"snapshot/{sid}?format=json") if st == "ready" else []
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(data, ensure_ascii=False))
    print(f"✅ {len(data)} records → {out.relative_to(ROOT)}")
    return data

def parse(url):
    """Short links are resolved by yt-dlp; returns (handle, post_id)."""
    m = re.search(r"@([\w.]+)/video/(\d+)", url) or re.search(r"@([\w.]+)/video/(\d+)", subprocess.run(
        ["yt-dlp", "--get-url", "--print", "webpage_url", "--skip-download", url], capture_output=True, text=True).stdout)
    return m.group(1), m.group(2)

def run(*a):
    return subprocess.run([str(x) for x in a], capture_output=True, text=True).stderr

def rms(video, a, b):
    out = run("ffmpeg", "-hide_banner", "-i", video, "-af", f"atrim={a}:{b},astats=metadata=0", "-f", "null", "-")
    v = re.findall(r"RMS level dB: (-?[\d.]+|-inf)", out)
    return float(v[-1]) if v and v[-1] != "-inf" else -99.0

def sound_of(handle, pid):
    """Music info for a post from any saved Bright Data posts file of the channel."""
    for f in sorted((ROOT / "stats/refs" / handle).glob("*post*.json"), reverse=True):
        for p in json.loads(f.read_text()):
            if pid in (p.get("url") or "") and p.get("music"):
                return p["music"]
    return {}

def video(url):
    handle, pid = parse(url)
    work = ROOT / "research/work" / handle / pid; work.mkdir(parents=True, exist_ok=True)
    mp4 = work / "v.mp4"
    if not mp4.exists():
        print("📥 downloading", flush=True)
        run("yt-dlp", "-q", "-o", work / "v.%(ext)s", "--write-info-json", f"https://www.tiktok.com/@{handle}/video/{pid}")
    info = json.loads((work / "v.info.json").read_text())
    dst = DRIVE / "references/tiktok" / handle; dst.mkdir(parents=True, exist_ok=True)
    name = f"{info.get('view_count') or 0}_{pid}"
    if not list(dst.glob(f"*_{pid}.mp4")):
        shutil.copy(mp4, dst / f"{name}.mp4"); shutil.copy(work / "v.info.json", dst / f"{name}.info.json")
    print("🎞️  frames + cuts", flush=True)
    run("ffmpeg", "-y", "-i", mp4, "-t", "3", "-vf", "fps=4,scale=240:-2,tile=6x2", "-frames:v", "1", work / "hook.png")
    dur = float(info.get("duration") or 0)
    rows = max(1, int(dur // 10) + 1)
    run("ffmpeg", "-y", "-i", mp4, "-vf", f"fps=1,scale=180:-2,tile=10x{rows}", "-frames:v", "1", work / "sheet.png")
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", run("ffmpeg", "-hide_banner", "-i", mp4, "-filter:v", "select='gt(scene,0.25)',showinfo", "-f", "null", "-"))]
    tj = work / "v.json"
    if not tj.exists():
        print("🗣️  whisper", flush=True)
        subprocess.run(WHISPER + [mp4, "--output-format", "json", "--output-dir", work], capture_output=True)
    segs = json.loads(tj.read_text())["segments"] if tj.exists() else []
    words = sum(len(s["text"].split()) for s in segs); spoken = sum(s["end"] - s["start"] for s in segs)
    gaps = [(a["end"], b["start"]) for a, b in zip(segs, segs[1:]) if b["start"] - a["end"] >= 0.25]
    speech = statistics.median([rms(mp4, s["start"], s["end"]) for s in segs[:5]]) if segs else None
    gap = statistics.median([rms(mp4, a, b) for a, b in gaps[:5]]) if gaps else None
    music = sound_of(handle, pid)
    if music.get("id"):
        mdir = DRIVE / "music"; slug = "_".join(re.sub(r"[^a-z0-9]+", "-", (music.get(k) or "").lower()).strip("-") for k in ("title", "authorname"))[:60]
        if not list(mdir.glob(f"{music['id']}_*")):
            run("ffmpeg", "-y", "-i", mp4, "-vn", "-c:a", "copy", mdir / f"{music['id']}_{slug}.m4a")
    summary = {"handle": handle, "post_id": pid, "views": info.get("view_count"), "likes": info.get("like_count"),
               "comments": info.get("comment_count"), "shares": info.get("repost_count"), "saves": info.get("save_count"),
               "posted": datetime.datetime.fromtimestamp(info["timestamp"], datetime.UTC).date().isoformat() if info.get("timestamp") else None,
               "duration_s": dur, "hard_cuts": len(cuts), "cut_times": [round(c, 1) for c in cuts],
               "lang": json.loads(tj.read_text()).get("language") if tj.exists() else None,
               "voice_wpm": round(words / spoken * 60) if spoken else 0,
               "speech_db": speech, "gap_db": gap, "music_bed_guess": None if gap is None else "none" if gap < -45 else "quiet" if speech - gap > 6 else "loud",
               "sound": {k: music.get(k) for k in ("id", "title", "authorname", "original")},
               "description": info.get("description"), "drive_video": f"02_sources/references/tiktok/{handle}/{name}.mp4",
               "transcript": " ".join(s["text"].strip() for s in segs), "work": str(work)}
    (work / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))

def post_of(handle, pid):
    for f in sorted((ROOT / "stats/refs" / handle).glob("*post*.json"), reverse=True):
        for p in json.loads(f.read_text()):
            if pid in (p.get("url") or ""):
                return p
    sys.exit(f"❌ {pid} not in saved posts of @{handle}: run `ref.py posts {handle}` first")

def photo(url):
    """Photo carousel: images + sound come from the saved Bright Data post (yt-dlp can't fetch photo posts)."""
    handle, pid = re.search(r"@([\w.]+)/(?:photo|video)/(\d+)", url).groups()
    p = post_of(handle, pid)
    work = ROOT / "research/work" / handle / pid; work.mkdir(parents=True, exist_ok=True)
    imgs = []
    for i, src in enumerate(p.get("carousel_images") or [], 1):
        f = work / f"{i:02d}.jpg"
        if not f.exists():
            urllib.request.urlretrieve(src, f)
        imgs.append(f)
    print(f"🖼️  {len(imgs)} slides", flush=True)
    run("ffmpeg", "-y", *sum([["-i", f] for f in imgs], []), "-filter_complex",
        "".join(f"[{i}]scale=360:-2,pad=360:640:(ow-iw)/2:(oh-ih)/2[s{i}];" for i in range(len(imgs))) + "".join(f"[s{i}]" for i in range(len(imgs))) + f"hstack={len(imgs)}" if len(imgs) > 1 else "[0]scale=360:-2",
        "-frames:v", "1", work / "sheet.png")
    dst = DRIVE / "references/tiktok" / handle / f"{p['play_count']}_{pid}"
    if not dst.exists():
        dst.mkdir(parents=True); [shutil.copy(f, dst / f.name) for f in imgs]
    m = p.get("music") or {}
    if m.get("playurl"):
        slug = "_".join(re.sub(r"[^a-z0-9]+", "-", (m.get(k) or "").lower()).strip("-") for k in ("title", "authorname"))[:60]
        if not list((DRIVE / "music").glob(f"{m['id']}_*")):
            urllib.request.urlretrieve(m["playurl"], DRIVE / "music" / f"{m['id']}_{slug}.mp3")
    n = lambda k: int(p.get(k) or 0)
    summary = {"handle": handle, "post_id": pid, "views": p["play_count"], "likes": n("digg_count"), "comments": n("comment_count"),
               "shares": n("share_count"), "saves": n("collect_count"), "posted": p["create_time"][:10], "slides": len(imgs),
               "sound": {k: m.get(k) for k in ("id", "title", "authorname", "original")}, "description": p.get("description"),
               "drive_video": str(dst.relative_to(DRIVE.parent)), "work": str(work)}
    (work / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "posts":
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        scrape("posts", [{"url": f"https://www.tiktok.com/@{arg}", "num_of_posts": n}], ROOT / f"stats/refs/{arg}/{TODAY}_posts.json", True)
    elif cmd == "profile":
        scrape("profile", [{"url": f"https://www.tiktok.com/@{arg}"}], ROOT / f"stats/refs/{arg}/{TODAY}_profile.json")
    elif cmd == "comments":
        h, pid = parse(arg)
        scrape("comments", [{"url": f"https://www.tiktok.com/@{h}/video/{pid}"}], ROOT / f"stats/refs/{h}/{TODAY}_comments_{pid}.json")
    elif cmd == "video":
        video(arg)
    elif cmd == "photo":
        photo(arg)
