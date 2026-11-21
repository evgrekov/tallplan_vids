"""Whole-slide generation through fal (art, diagrams and texts in one image). Usage: full.py POST SLIDE... [--q low|medium]"""
import os, sys, json, glob, time, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = [l.split("=", 1)[1].strip() for l in open(ROOT + "/.env") if l.startswith("FAL_KEY=")][0]
args = [a for a in sys.argv[1:] if not a.startswith("--")]; q = sys.argv[sys.argv.index("--q") + 1] if "--q" in sys.argv else "low"
if "--q" in sys.argv: args.remove(q)
post, slides = args[0], args[1:]
pdir = glob.glob(f"{ROOT}/top10/{post}_*")[0]; out = f"{ROOT}/gen/{post}"; os.makedirs(out, exist_ok=True)

def where(b, W=100, H=100):
    cx, cy = b[0] + b[2] / 2, b[1] + b[3] / 2
    return f'{"top" if cy < 33 else "middle" if cy < 66 else "bottom"} {"left" if cx < 33 else "center" if cx < 66 else "right"}'

def prompt(s):
    portrait = s["canvas"]["aspect_ratio"] == "9:16"
    texts = "\n".join(f'- "{t["text"].replace("GoTall", "TallPlan")}" ({where(t["bbox_pct"])}, {"large heading" if t["size_pct_of_height"] > 8 else "medium" if t["size_pct_of_height"] > 4 else "small label"})' for t in s["texts"])
    gfx = " ".join(g["description"].rstrip(".") + "." for g in s["graphics"])
    ill = s["illustration"]["description"] if s["illustration"]["present"] else ""
    return (f"A {'vertical 9:16' if portrait else 'square'} educational infographic slide for a TikTok carousel about height growth. "
            f"Clean flat editorial design on a warm off-white paper background (#f3f2ec) with a very faint grid. Text in dark green ink (#12251c), accents in green (#1f7a4d), bold condensed grotesque sans-serif for headings, simple sans-serif for labels. "
            f"Illustration/diagram: {ill} Other graphic elements: {gfx} "
            f"Render exactly this text, spelled correctly, and no other text, logos or watermarks. Each listed text appears exactly once, with no duplicated rows or labels and no stray characters:\n{texts}")

def gen(n):
    s = json.load(open(f"{pdir}/{n}.json")); portrait = s["canvas"]["aspect_ratio"] == "9:16"
    body = {"prompt": prompt(s), "quality": q, "image_size": {"width": 1152, "height": 2048} if portrait else {"width": 2048, "height": 2048}, "background": "opaque"}
    req = urllib.request.Request("https://fal.run/openai/gpt-image-2.5/flare/text-to-image", json.dumps(body).encode(), {"Authorization": "Key " + KEY, "Content-Type": "application/json"})
    for attempt in range(8):
        try: url = json.load(urllib.request.urlopen(req, timeout=300))["images"][0]["url"]; break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 7: raise
            time.sleep(8 * (attempt + 1))
    open(f"{out}/{n}.png", "wb").write(urllib.request.urlopen(url).read()); print("✅", post, n, q)

for n in slides: gen(n)
