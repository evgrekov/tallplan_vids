import re, os, sys, json, glob, time, urllib.request, urllib.error, subprocess, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = [l.split("=",1)[1].strip() for l in open(ROOT+"/.env") if l.startswith("FAL_KEY=")][0]
ASSETS = ROOT + "/TallPlan photo"
post = glob.glob(ROOT + "/top10/" + sys.argv[1] + "_*")[0]
out = ROOT + "/gen/" + sys.argv[1]; os.makedirs(out, exist_ok=True)
slides = sys.argv[2:] or sorted(os.path.basename(f)[:2] for f in glob.glob(post + "/[0-9][0-9].json"))
r16 = lambda v: max(16, round(v/16)*16)

def art_graphics(s):
    top = s["illustration"]["bbox_pct"][1]
    return [g for g in s["graphics"] if not (g["bbox_pct"][3] < 1.5 and g["bbox_pct"][1] < top)]

def art_box(s):
    bs = [s["illustration"]["bbox_pct"]] + [g["bbox_pct"] for g in art_graphics(s)]
    x0, y0 = min(b[0] for b in bs), min(b[1] for b in bs)
    x1, y1 = max(b[0] + b[2] for b in bs), max(b[1] + b[3] for b in bs)
    if (x1 - x0) / (y1 - y0) > 5:  # the recogniser sometimes returns a thin strip: use the free band between heading and caption instead
        top = max([t["bbox_pct"][1] + t["bbox_pct"][3] for t in s["texts"] if t["bbox_pct"][1] < 30] or [0]) + 3
        low = min([t["bbox_pct"][1] for t in s["texts"] if t["bbox_pct"][1] > 60] or [97]) - 3
        return [x0, top, x1 - x0, low - top]
    return [x0, y0, x1 - x0, y1 - y0]

def fit_box(s):
    """Art box trimmed so no text bbox overlaps it (the art keeps its aspect via object-contain, so it just gets smaller)."""
    x, y, w, h = art_box(s)
    for t in s["texts"]:
        tx, ty, tw, th = t["bbox_pct"]
        if tx < x + w and tx + tw > x and ty < y + h and ty + th > y:
            if ty + th / 2 > y + h / 2: h = max(10, ty - y - 1)   # caption below -> end the art above it
            else: h -= ty + th + 1 - y; y = ty + th + 1             # caption above -> start the art below it
    return [x, y, w, h]

def gen(n, s):
    if os.path.exists(f"{out}/{n}_illustration.png"): return  # keep existing art on re-render
    il = s["illustration"]; _, _, w, h = art_box(s)
    ratio = min(3, max(1/3, w/h)); W = 1536 if ratio >= 1 else 1536*ratio; H = W/ratio
    body = {"prompt": il["description"] + " Include these infographic elements drawn in the same image, in a clean flat vector style: " + " ".join(f'{g["description"]}.' for g in art_graphics(s)) + " Plain pure white background. No text, no letters, no numbers.", "quality": "low",
            "image_size": {"width": r16(W), "height": r16(H)}, "background": "opaque"}
    req = urllib.request.Request("https://fal.run/openai/gpt-image-2.5/flare/text-to-image", json.dumps(body).encode(),
        {"Authorization": "Key " + KEY, "Content-Type": "application/json"})
    for attempt in range(8):  # fal answers 429 when several posts render at once
        try: url = json.load(urllib.request.urlopen(req, timeout=300))["images"][0]["url"]; break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 7: raise
            time.sleep(8 * (attempt + 1))
    open(f"{out}/{n}_illustration.png", "wb").write(urllib.request.urlopen(url).read())

def brand(c):  # map the original slide colours onto the TallPlan palette: orange accent -> green, black text -> ink
    r, g, b = (int(c[i:i+2], 16) for i in (1, 3, 5))
    return "var(--green)" if r > 180 and b < 120 else "var(--ink)" if max(r, g, b) < 90 else c

def box(b): return f"left:{b[0]}%;top:{b[1]}%;width:{b[2]}%;height:{b[3]}%"

def last_slide(s, H):
    """Last-slide template (phone + logo + app name + CTA): big headline on top, phone on the left, logo/name/CTA stacked on the right (square) or in a row below the phone (portrait)."""
    portrait = H != 1080
    fix = lambda t: re.sub(r"(?i)link in bio\W*", "Search TallPlan in the stores", t["text"]).replace("GoTall", "TallPlan")  # there is no link in bio
    ts = sorted(s["texts"], key=lambda t: t["bbox_pct"][1])
    top = [t for t in ts if t["bbox_pct"][1] < 40]; low = [t for t in ts if t["bbox_pct"][1] >= 60 and fix(t).strip().lower() != "tallplan"]
    import math
    bigs = [t for t in top if t["size_pct_of_height"] > 8] or top[:1]; smalls = [t for t in top if t not in bigs]  # no big text -> the first one is the heading
    sub = " ".join(fix(t) for t in smalls)
    cta = "<br>".join(fix(t) for t in low)
    if len(bigs) >= 2: lines = [fix(t) for t in bigs]
    else:  # one long heading: split it evenly (2 lines square, 3 portrait)
        words = (fix(bigs[0]) if bigs else "Maximize your height").split(); n = min(len(words), 3 if portrait else 2); per = math.ceil(len(words) / n)
        lines = [" ".join(words[i:i + per]) for i in range(0, len(words), per)]
    base = 150 if portrait else 132
    fs = min(base, int(960 / (0.58 * max(len(l) for l in lines))))
    h1 = "<br>".join(lines[:-1] + [f'<span class="text-[var(--green)]">{lines[-1]}</span>'])
    head_h = int(len(lines) * fs * .94); sub_y = 40 + head_h + 24; sub_fs = 54 if portrait else 38
    y_after = sub_y + (sub_fs + 36 if sub else 0)
    m = open(ROOT + "/gen/phone_matrix.txt").read()
    vis_y = y_after + 10; vis_h = min(1000, 1500 - vis_y) if portrait else min(700, 1040 - vis_y); vis_x = 190 if portrait else 90  # visible phone box (px)
    sc = vis_h / 1100; lx, ty = vis_x - 165 * sc, vis_y - 130 * sc
    if portrait: lx = (1080 - 575 * sc) / 2 - 165 * sc
    phone = (f'<div class="absolute" style="left:{lx}px;top:{ty}px;width:900px;height:1343px;transform:scale({sc});transform-origin:0 0;filter:drop-shadow(0 0 40px #10c97aaa) drop-shadow(-20px 30px 30px #0005)">'
             f'<div class="absolute inset-0" style="-webkit-mask-image:url(file://{ROOT}/gen/hole_mask.png);mask-image:url(file://{ROOT}/gen/hole_mask.png)"><img src="file://{ASSETS}/Screenshots/iOS/today.png" class="absolute" style="left:0;top:0;width:1206px;max-width:none;height:2622px;border-radius:146px;transform-origin:0 0;transform:{m}"></div>'
             f'<img src="file://{ROOT}/gen/iphone_cut.png" class="absolute inset-0 w-full h-full"></div>')
    logo = lambda sz, x, y: f'<img src="file://{ASSETS}/Logo/app-icon.png" class="absolute rounded-[22%]" style="left:{x}px;top:{y}px;width:{sz}px;height:{sz}px;transform:rotate(6deg);box-shadow:-12px 16px 28px #0006,0 0 60px #10c97a99">'
    name = lambda fs, x, y, w, al: f'<div class="absolute display normal-case text-[var(--ink)]" style="left:{x}px;top:{y}px;width:{w}px;font-size:{fs}px;text-align:{al};line-height:1">Tall<span class="text-[var(--green)]">Plan</span></div>'
    txt = lambda c, fs, x, y, w, al, extra="": f'<div class="absolute {c}" style="left:{x}px;top:{y}px;width:{w}px;font-size:{fs}px;text-align:{al};{extra}">'
    col_y = int(vis_y + (vis_h - 560) / 2)  # right column (logo, name, CTA) is centred on the phone
    if portrait:
        body = (txt("display uppercase text-[var(--ink)]", fs, 40, 40, 1000, "center", "line-height:.94") + h1 + "</div>"
                + (txt("font-bold text-[var(--ink)]", sub_fs, 40, sub_y, 1000, "center", "letter-spacing:.06em") + sub + "</div>" if sub else "")
                + phone + logo(190, 190, 1500) + name(160, 410, 1530, 560, "left")
                + (txt("display uppercase text-[var(--ink)]", 60, 40, 1740, 1000, "center", "line-height:1.05") + cta + "</div>" if cta else ""))
    else:
        body = (txt("display uppercase text-[var(--ink)]", fs, 40, 40, 1000, "center", "line-height:.94") + h1 + "</div>"
                + (txt("font-bold text-[var(--ink)]", sub_fs, 40, sub_y, 1000, "center", "letter-spacing:.06em") + sub + "</div>" if sub else "")
                + phone + logo(250, 640, col_y) + name(112, 540, col_y + 280, 450, "center")
                + (txt("display uppercase text-[var(--ink)]", 50, 540, col_y + 420, 450, "center") + cta + "</div>" if cta else ""))
    return f'''<!doctype html><html><head><meta charset="utf-8"><script src="https://cdn.tailwindcss.com/3.4.17"></script>
<link rel="stylesheet" href="file://{ROOT}/gen/brand.css"><style>html,body{{margin:0}}</style></head>
<body><div class="relative w-[1080px] h-[{H}px] bg-[var(--paper)] overflow-hidden font-['Archivo']">{body}</div></body></html>'''

def html(n, s):
    p = []
    H = 1920 if s["canvas"]["aspect_ratio"] == "9:16" else 1080  # post 10 is a portrait 9:16 carousel
    il = s["illustration"]
    if il["present"]:
        p.append(f'<img src="{n}_illustration.png" class="absolute mix-blend-multiply object-contain" style="{box(fit_box(s))}">')
    for t in s["texts"]:
        big = t["size_pct_of_height"] > 8
        cls = "display uppercase" if big else "font-bold"
        p.append(f'<div class="absolute fit whitespace-nowrap text-center {cls}" data-h="{t["size_pct_of_height"]}" style="{box(t["bbox_pct"])};color:{brand(t["color"])};display:flex;align-items:center;justify-content:{"flex-end" if t["text"].rstrip(".").isdigit() else "center"};{"letter-spacing:.06em" if t["text"].rstrip(".").isdigit() else ""}">{t["text"].replace("GoTall", "TallPlan")}</div>')  # old brand name in the source slides
    svg = []
    for g in art_graphics(s) if False else [g for g in s["graphics"] if g not in art_graphics(s)] if il["present"] else s["graphics"]:
        if not il["present"] and g["type"] not in ("line", "chevron"): continue  # arrows/glows/shapes need art or are baked into the mockup
        x, y, w, h = g["bbox_pct"]; c = brand(g["color"]) if not il["present"] or g not in art_graphics(s) else g["color"]; d = g["description"].lower()
        if g["type"] == "line":
            if "dashed" in d: svg.append(f'<path d="M{x} {y+h/2}h{w}" stroke="{c}" stroke-width=".3" stroke-dasharray="1.2 .8"/>')
            else: svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{max(h,.4)}" fill="{c}"/>')
        elif g["type"] == "chevron":
            dr = -1 if "pointing left" in d else 1; m = x + (w if dr < 0 else 0); cw = w * .5
            svg.append("".join(f'<path d="M{m+dr*k*cw*.9} {y}L{m+dr*(k*cw*.9+cw*.8)} {y+h/2}L{m+dr*k*cw*.9} {y+h}" stroke="{c}" stroke-width=".9" fill="none" stroke-linejoin="round" stroke-linecap="round"/>' for k in (0, 1)))
        else:  # arrow / dotted trail: dotted quadratic arc, head rotated along the end tangent
            import math
            if h > 2 * w:  # vertical arrow: straight dotted shaft, head at the end named in the description
                up = "downward" not in d and "down" not in d.split("ending")[0]
                cx_ = x + w / 2; ya, yb = (y + h, y) if up else (y, y + h); sg = -1 if up else 1
                svg.append(f'<path d="M{cx_} {ya}V{yb-sg*3.2}" stroke="{c}" stroke-width=".8" stroke-dasharray="0 1.8" stroke-linecap="round"/>'
                           f'<path d="M{cx_-2.8} {yb-sg*5}h5.6L{cx_} {yb}z" fill="{c}"/>')
                continue
            x0, y0, cx, cy, x1, y1 = x, y + h, x + w * .5, y - h * .3, x + w, y
            ang = math.degrees(math.atan2(y1 - cy, x1 - cx)); r = math.radians(ang)
            ex, ey = x1 - 3.2 * math.cos(r), y1 - 3.2 * math.sin(r)  # dotted line stops before the head
            svg.append(f'<path d="M{x0} {y0}Q{cx} {cy} {ex} {ey}" stroke="{c}" stroke-width=".8" stroke-dasharray="0 1.8" stroke-linecap="round" fill="none"/>')
            if g["type"] != "dotted_trail":
                svg.append(f'<path d="M-2.4 -1.9L2.4 0L-2.4 1.9z" fill="{c}" transform="translate({x1} {y1}) rotate({ang})"/>')
    for i in s["inserts"]:
        k = i["kind"]; b = i["bbox_pct"]
        if k == "logo":
            # house rule: the last slide always carries the app name under the logo
            if not any(w in t["text"].lower() for t in s["texts"] for w in ("tallplan", "gotall")):  # slide already names the app
              p.append(f'<div class="absolute text-center display normal-case text-[var(--ink)]" style="left:{b[0]-6}%;width:{b[2]+12}%;top:{b[1]+b[3]+3.5}%;font-size:92px;letter-spacing:.01em">Tall<span class="text-[var(--green)]">Plan</span></div>')
            p.append(f'<div class="absolute" style="{box(b)};perspective:900px"><img src="file://{ASSETS}/Logo/app-icon.png" class="w-full h-full rounded-[22%]" style="transform:rotateY(-22deg) rotateX(10deg) rotateZ(6deg);box-shadow:-14px 18px 30px #0006,0 0 60px #10c97a99,inset 0 0 0 2px #ffffff55"></div>')
        elif k == "app_screenshot":
            # real iPhone mockup (gen/iphone_cut.png): screenshot is perspective-warped (matrix3d) into the screen quad and sits under the frame
            m = open(ROOT + "/gen/phone_matrix.txt").read()
            sc = b[3] * H / 100 / 1100 if H != 1080 else .52  # visible phone is ~1100 of the 1343 frame px
            lx, ty = (b[0] * 10.8 - 165 * sc, b[1] * H / 100 - 130 * sc) if H != 1080 else (64, 310)
            p.append(f'<div class="absolute" style="left:{lx}px;top:{ty}px;width:900px;height:1343px;transform:scale({sc});transform-origin:0 0;filter:drop-shadow(0 0 40px #10c97aaa) drop-shadow(-20px 30px 30px #0005)">'
                     f'<div class="absolute inset-0" style="-webkit-mask-image:url(file://{ROOT}/gen/hole_mask.png);mask-image:url(file://{ROOT}/gen/hole_mask.png)"><img src="file://{ASSETS}/Screenshots/iOS/today.png" class="absolute" style="left:0;top:0;width:1206px;max-width:none;height:2622px;border-radius:146px;transform-origin:0 0;transform:{m}"></div>'
                     f'<img src="file://{ROOT}/gen/iphone_cut.png" class="absolute inset-0 w-full h-full"></div>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><script src="https://cdn.tailwindcss.com/3.4.17"></script>
<link rel="stylesheet" href="file://{ROOT}/gen/brand.css"><style>html,body{{margin:0}}</style></head>
<body><div class="relative w-[1080px] h-[{H}px] bg-[var(--paper)] overflow-hidden font-['Archivo']">{"".join(p)}
<svg class="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">{"".join(svg)}</svg></div>
<script>document.fonts.ready.then(()=>{{document.querySelectorAll('.fit').forEach(e=>{{let fs=+e.dataset.h*{H}/100*(e.classList.contains('display')?1.0:.95);e.style.fontSize=fs+'px';
const W=e.clientWidth;while(e.scrollWidth>W*1.0&&fs>10){{fs-=2;e.style.fontSize=fs+'px'}}}});document.title='ok'}})</script></body></html>'''

specs = {n: json.load(open(f"{post}/{n}.json")) for n in slides}
with cf.ThreadPoolExecutor(6) as ex:
    list(ex.map(lambda a: gen(*a), [(n, s) for n, s in specs.items() if s["illustration"]["present"]]))
for n, s in specs.items():
    Hs = 1920 if s["canvas"]["aspect_ratio"] == "9:16" else 1080
    open(f"{out}/{n}.html", "w").write(last_slide(s, Hs) if any(i["kind"] == "app_screenshot" for i in s["inserts"]) else html(n, s))
    subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars",
        "--virtual-time-budget=10000", "--force-device-scale-factor=2", "--window-size=1080," + str(1920 if s["canvas"]["aspect_ratio"] == "9:16" else 1080), f"--screenshot={out}/{n}.png", f"file://{out}/{n}.html"], capture_output=True)
    print("✅", n)
