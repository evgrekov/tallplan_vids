"""One static style-test frame of the layout format: CEO vs CMO, speech bubbles, engine cards."""
from PIL import Image, ImageDraw, ImageFont
from people import CEO, CMO, Character

W, H = 1080, 1920
F = "fonts/Display.ttf"
def font(s, w=900):
    f = ImageFont.truetype(F, s)
    try: f.set_variation_by_axes([w])
    except OSError: pass
    return f

img = Image.new("RGBA", (W, H), "#eef1f7"); d = ImageDraw.Draw(img)
for x in range(30, W, 60):  # dot grid
    for y in range(30, H, 60): d.ellipse((x - 2, y - 2, x + 2, y + 2), fill="#d9deea")

d.text((W / 2, 150), "ARE WE #1 IN AI?", font=font(96), fill="#101828", anchor="mm")
d.text((W / 2, 250), "the CEO asked", font=font(44, 500), fill="#667085", anchor="mm")

cards = [("chatgpt", "Brand A"), ("gemini", "Brand C"), ("google-ai-mode", "Brand B")]
for i, (eng, brand) in enumerate(cards):
    x, y = 70 + i * 320, 350
    d.rounded_rectangle((x + 6, y + 10, x + 306, y + 330), 32, fill="#d5dbe8")
    d.rounded_rectangle((x, y, x + 300, y + 320), 32, fill="#ffffff")
    l = Image.open(f"logos/{eng}.png").convert("RGBA"); l = l.resize((90, round(90 * l.height / l.width)))
    img.alpha_composite(l, (x + 105, y + 40))
    d.text((x + 150, y + 175), "#1", font=font(40, 700), fill="#667085", anchor="mm")
    d.rounded_rectangle((x + 30, y + 215, x + 270, y + 285), 20, fill="#2563eb" if i == 0 else "#101828")
    d.text((x + 150, y + 250), brand, font=font(42, 800), fill="#ffffff", anchor="mm")

d.text((W / 2, 790), "36%", font=font(170), fill="#2563eb", anchor="mm")
d.text((W / 2, 900), "of prompts: all three agree on #1", font=font(44, 600), fill="#101828", anchor="mm")

floor = 1830
for ch, pose, cx in ((CEO, {"prop": "phone", "ra": (12, 130), "look": 1, "brows": -1}, 290),
                     (CMO, {"la": (22, 55), "ra": (22, 55), "brows": 1, "tilt": -2, "look": -1}, 790)):
    c = ch.render(pose, 740); fx, fy = Character.feet(740)
    d.ellipse((cx - 150, floor - 18, cx + 150, floor + 18), fill="#d5dbe8")
    img.alpha_composite(c, (round(cx - fx), round(floor - fy)))

def bubble(x, y, s, tail):
    f = font(48, 800); w = f.getlength(s)
    d.rounded_rectangle((x - w / 2 - 36, y - 46, x + w / 2 + 36, y + 46), 46, fill="#101828")
    d.polygon([(tail, y + 40), (tail + 40, y + 40), (tail + 10, y + 90)], fill="#101828")
    d.text((x, y), s, font=f, fill="#ffffff", anchor="mm")
bubble(760, 1040, "Which one?", 800)

img.convert("RGB").save("out/test-frame.jpg", quality=92)
