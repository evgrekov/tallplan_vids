# /// script
# dependencies = ["pillow"]
# ///
"""Google App campaign video #10 "group chat is chaos": friends post their TallPlan prediction cards in an unbranded group chat,
I check mine in the app (locked → reveal → share) and drop it in the chat → end card "Check yours".
Usage: uv run gads/groupchat.py   (idempotent: voice/music/sfx are cached in gads/groupchat/)
"""
import subprocess
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw
import kit
from kit import SW, SH, archivo, ease, zoom, tap, rich, width

D = kit.ROOT / "gads/groupchat"
kit.CAP_Y = 0.21  # over the static chat header: new messages arrive at the bottom
PEOPLE = {"Jay": (90, 120, 255), "Mia": (255, 120, 170), "Sam": (255, 170, 60), "me": None}
# (time, who, text or ("card", height, top %, inches to go)); app cut sits between "checking rn" and my card
CHAT = [(0.2, "Jay", "ok everyone post your predicted heights \U0001F440"),
        (0.9, "Jay", ("card", "6'0\"", 22, 3)),
        (1.6, "Mia", ("card", "5'7\"", 30, 2)),
        (2.2, "Sam", "WAIT"),
        (2.6, "Sam", ("card", "5'11\"", 40, 4)),
        (3.3, "Mia", "sam said WAIT like a plot twist \U0001F62D"),
        (4.0, "Jay", "where's yours"),
        (4.6, "me", "checking rn")]
APP = (5.1, 9.0)  # locked → reveal → share screen
AFTER = [(9.2, "me", "SHARE"), (9.9, "Sam", "6'3??? \U0001F480"), (10.6, "Mia", "ok we're all checking again")]
CHAT += AFTER
REACT = {(9.4, 11.2): "\U0001F525"}  # fire tapback on my card
END = 11.2

LOCKED = Image.open(kit.SHOTS / "01-home-locked.png").convert("RGB")
HOME = Image.open(kit.SHOTS / "01-home.png").convert("RGB")
SHARE = Image.open(kit.SHOTS / "03-share-card.png").convert("RGB")
MYCARD = SHARE.crop((270, 660, 1050, 2044))
BAR = kit.bar("8:42")

def card(h, top, inches):
    """A friend's share card drawn in the app's style (same size as the real one)."""
    w, H = MYCARD.size
    c = Image.new("RGB", (w, H)); d = ImageDraw.Draw(c)
    for y in range(H):  # blue gradient like the app card
        k = y / H; d.line((0, y, w, y), fill=(round(44 - 34 * k), round(70 - 60 * k), round(190 - 120 * k)))
    d.text((80, 260), "Heading for", font=archivo(58, 800), fill="white")
    d.text((70, 320), h, font=archivo(190, 900), fill="white")
    d.rounded_rectangle((80, 550, 300, 620), 35, fill="white"); d.text((190, 585), f"+{inches} in to go", font=archivo(32, 800), fill=(20, 30, 90), anchor="mm")
    d.rounded_rectangle((80, 610 + 50, w - 80, 920), 40, fill=(20, 30, 90))
    d.text((120, 700), f"Top {top}%", font=archivo(76, 850), fill="white")
    me = 10 - top // 10
    for i in range(11):
        x = 120 + i * 50; bh = 50 + i * 8
        d.rounded_rectangle((x, 880 - bh, x + 36, 880), 10, fill=kit.LIME if i == me else (140, 145, 175))
    wm = Image.open(kit.LOGO / "wordmark.png"); wm = wm.resize((220, 73), Image.LANCZOS)
    c.paste(wm, ((w - 220) // 2, 1010), wm)
    return c

TXT = archivo(72, 500)
def bubble(t, who, body):
    """Message as an RGBA tile + whether it is mine."""
    mine = who == "me"
    if isinstance(body, tuple):
        im = MYCARD if body[0] == "mine" else card(*body[1:])
        im = im.resize((440, round(440 * im.height / im.width)), Image.LANCZOS)
        m = Image.new("L", im.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 50, fill=255)
        tile = Image.new("RGBA", im.size); tile.paste(im, (0, 0), m)
    else:
        lines = [""]
        for w in body.split():  # wrap to a bubble of at most ~880 px
            if width(f"{lines[-1]} {w}", TXT) < 880: lines[-1] = f"{lines[-1]} {w}".strip()
            else: lines.append(w)
        lh = 90
        tile = Image.new("RGBA", (round(max(width(l, TXT) for l in lines)) + 80, lh * len(lines) + 50))
        ImageDraw.Draw(tile).rounded_rectangle((0, 0, tile.width - 1, tile.height - 1), 60, fill=(48, 84, 235) if mine else (38, 39, 45))
        for j, l in enumerate(lines): rich(tile, (40, 22 + j * lh), l, TXT, "white")
    return tile, mine

_tiles = {}
def chat(t):
    """Unbranded group chat: header, messages that pop in from the bottom, typing dots, a tapback."""
    im = Image.new("RGB", (SW, SH), kit.BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, SH - 230, SW - 60, SH - 110), 60, outline=(60, 62, 70), width=4)
    d.text((120, SH - 170), "Message", font=archivo(56, 500), fill=(110, 112, 120), anchor="lm")
    bubbles(im, d, t)
    d.rectangle((0, 0, SW, 450), fill=kit.BG); im.paste(BAR, (0, 0))  # header drawn last so scrolled bubbles slide under it
    for i, (n, col) in enumerate([(n, c) for n, c in PEOPLE.items() if c]):  # group avatars: initials only, no faces
        x = SW / 2 - 110 + i * 110
        d.ellipse((x - 60, 210, x + 60, 330), fill=col, outline=kit.BG, width=8); d.text((x, 270), n[0], font=archivo(60, 850), fill="white", anchor="mm")
    d.text((SW / 2, 380), "the group chat", font=archivo(52, 800), fill="white", anchor="mm")
    d.line((0, 450, SW, 450), fill=(30, 31, 36), width=3)
    return im

def bubbles(im, d, t):
    shown = [(i, m) for i, m in enumerate(CHAT) if m[0] <= t]
    y = SH - 280
    nxt = next((m for m in CHAT if m[0] > t), None)
    if nxt and nxt[1] != "me" and nxt[0] - t < 0.45:  # typing dots before a friend's message
        y -= 110
        d.rounded_rectangle((150, y, 330, y + 100), 50, fill=(38, 39, 45))
        for j in range(3):
            a = 120 + int(100 * (((t * 3 - j * 0.3) % 1) < 0.5)); d.ellipse((190 + j * 50, y + 38, 214 + j * 50, y + 62), fill=(a, a, a + 8))
    for i, (st, who, body) in reversed(shown):
        if i not in _tiles: _tiles[i] = bubble(st, who, body if body != "SHARE" else ("mine",))
        tile, mine = _tiles[i]
        k = ease((t - st) / 0.18)
        named = not mine and (CHAT[i - 1][1] if i else None) != who  # a friend's first bubble in a row gets avatar + name
        y -= tile.height + 26
        if y + tile.height < 450: break
        x = SW - 60 - tile.width if mine else 150
        if k < 1:
            tile = tile.resize((max(1, round(tile.width * (0.85 + 0.15 * k))), max(1, round(tile.height * (0.85 + 0.15 * k)))))
            tile.putalpha(tile.getchannel("A").point(lambda v: int(v * k)))
        im.paste(tile, (x, round(y + 40 * (1 - k))), tile)
        if named:
            d.ellipse((50, y + tile.height - 80, 130, y + tile.height), fill=PEOPLE[who])
            d.text((90, y + tile.height - 40), who[0], font=archivo(44, 850), fill="white", anchor="mm")
            d.text((170, y - 50), who, font=archivo(40, 600), fill=(130, 132, 140))
            y -= 50
        if body == "SHARE":
            for (a, b), e in REACT.items():
                if a <= t < b: rich(im, (x - 40, y - 50), e, archivo(70), "white")

def app(t):
    """Locked home → tap → 6'3" reveal → share sheet with a tap on Share."""
    a, b = APP; u = t - a
    if u < 1.2:
        k = u / 1.2
        return zoom(tap(LOCKED, 658, 1244, (k - 0.6) / 0.35), 1 + 0.08 * ease(k), 0.5, 0.42)
    if u < 2.5:
        k = (u - 1.2) / 1.3
        im = zoom(HOME, 1 + 0.1 * ease(k), 0.5, 0.2)
        return Image.blend(im, Image.new("RGB", im.size, "white"), max(0, 0.7 * (1 - k * 6)))
    k = (u - 2.5) / (b - a - 2.5)
    return tap(SHARE, 660, 2596, (k - 0.55) / 0.35)

def screen(t): return app(t) if APP[0] <= t < APP[1] else chat(t)

def audio():
    """Voice hook + end line, a pop per message, meme music under it all."""
    hook = kit.say(D / "l1.wav", "We all checked our predicted heights. The group chat is chaos.", kit.TEEN + " Laughing a little.", speed=1.2)
    end = kit.say(D / "l2.wav", f"Check yours. {kit.CTA}!", kit.TEEN + " Hyped call to action.", speed=1.15)
    pop = D / "pop.wav"
    if not pop.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "aevalsrc='0.5*sin(2*PI*(1400-900*t/0.07)*t)*exp(-40*t)':d=0.12", str(pop)], check=True)
    kit.music(D / "music.mp3", "Funny modern TikTok meme beat, bouncy trap hi-hats, quirky plucked synth melody, playful and chaotic, 140 BPM, about 25 seconds.")
    cues = [("We all checked our predicted heights. The group chat is chaos.", 0.2, hook), (f"Check yours. {kit.CTA}!", END + 0.3, end)]
    total = END + 0.3 + end + 0.6
    assert hook < APP[0] and total <= kit.MAX, f"hook {hook:.1f}s, total {total:.1f}s"
    return cues, total, [(D / "l1.wav", 0.2), (D / "l2.wav", END + 0.3)] + [(pop, m[0]) for m in CHAT]

def build(fmt):
    W, H = kit.FORMATS[fmt]
    cues, total, _ = audio()
    kit.render(fmt, W, H, total, screen, cues, END, kit.CTA, "Estimate based on your data. Not medical advice.",
               D / "audio.wav", D / f"tallplan_groupchat_{fmt}.mp4")

if __name__ == "__main__":
    D.mkdir(exist_ok=True)
    cues, total, mixes = audio()
    kit.mix(mixes, D / "music.mp3", total, D / "audio.wav", vol=0.22)
    with ProcessPoolExecutor(3) as ex: list(ex.map(build, kit.FORMATS))
    print(f"💰 Google (Lyria) ~${kit.api.spent:.3f} · OpenAI (TTS) ~${kit.oai.spent:.3f}")
