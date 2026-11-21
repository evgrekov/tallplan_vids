#!/usr/bin/env python3
"""Reference TikTok → TallPlan ad, end to end. Every decision is an API call; prompt templates live in pipeline/prompts/.
Voice-first: TTS lines set the shot timecodes, the video model makes only SFX, Lyria makes the music.
Steps are idempotent: existing outputs are skipped, so delete a file to redo its step.
Usage: python3 auto.py <tiktok_url> <folder>
"""
import atexit, json, os, re, subprocess, sys
import align, api, voice
from api import ROOT, gemini, data, file

TPL = ROOT / "pipeline/prompts"
TRIES = 2
BUDGET = 2.0  # hard $ cap per ad, across reruns of the same folder (ledger: <folder>/spent.txt)
EST = {"image": 0.05, "base": 0.40, "ext": 0.40}  # worst case per try; 360p video ~$0.035/s
MAX_PARTS = 4  # base + 3 extensions = 34 s: longer references don't fit the budget

def afford(step):
    if api.spent + EST[step] > BUDGET:
        print(f"💸 budget ${BUDGET} would be exceeded by {step} (spent ~${api.spent:.2f})")
        return False
    return True

def run(*cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=os.environ | {"AD_BUDGET_LEFT": str(BUDGET - api.spent)})
    print(p.stdout.strip())
    if p.returncode and p.stderr.strip(): print(p.stderr.strip()[-500:])  # e.g. the API's reason for a failed generation
    api.spent += sum(float(x) for x in re.findall(r"💰 ~\$([\d.]+)", p.stdout))
    return p

def image_with_qa(out, prompt, refs, required=False):
    rejected = out.with_suffix(".rejected.png")
    if out.exists() or rejected.exists(): return
    for i in range(TRIES):
        if not afford("image"): sys.exit("💸 stopped before images")
        print(f"🖼️  {out.relative_to(d)} (try {i + 1})")
        out.write_bytes(data(gemini("gemini-3.1-flash-image", [*map(file, refs), {"text": prompt}],
                                    responseModalities=["IMAGE"], imageConfig={"aspectRatio": "9:16"})))
        if run("python3", ROOT / "qa.py", out).returncode == 0: return
    if required:  # the character image is the base of everything: keep the last try
        return print(f"⚠️  {out.name}: QA failed {TRIES}×, keeping last")
    out.rename(rejected)  # a broken keyframe (e.g. a second person) poisons the video: generate without it
    print(f"⚠️  {out.name}: QA failed {TRIES}×, not used")

def video_with_qa(out, prompt_file, images, prev=None, qa_from=0):
    idf = out.with_suffix(".id")
    if out.exists(): return idf.read_text()
    best = None  # (fails, file, id, speech): when no try passes, keep the one with the fewest confirmed defects
    for i in range(TRIES):
        if not afford("ext" if prev else "base"): break
        try_f = out.with_name(f"{out.stem}_try{i + 1}.mp4")
        p = run("python3", ROOT / "omni.py", prompt_file, try_f, *sum([["--image", x] for x in images], []), *(["--prev", prev] if prev else []))
        if "429" in p.stderr:  # daily video quota: retries only burn the next requests, stop and resume later (steps are idempotent)
            sys.exit(f"⏳ {out.name}: video model quota exhausted, rerun the same command later to continue")
        if not (m := re.search(r"id=(\S+)", p.stdout)):
            images = images[:1]  # keyframes trip the safety filter more often than the prompt: retry with the character only
            print(f"🔁 {out.name}: generation failed (try {i + 1}), next try without keyframes"); continue
        q = run("python3", ROOT / "qa.py", try_f, "--from", qa_from).stdout
        fails, speech = (int(re.search(rf"{k}=(\d+)", q).group(1)) for k in ("fails", "speech"))
        if best is None or fails < best[0]: best = (fails, try_f, m.group(1), speech)
        if not fails: break
        print(f"🔁 {out.name}: QA failed (try {i + 1})")
    if not best: sys.exit(f"❌ {out.name}: no usable generation (blocked or out of budget)")
    best[1].rename(out)
    idf.write_text(best[2])
    if best[3]: out.with_suffix(".speech").touch()  # the mix mutes this part's sound effects
    return best[2]

url, d = sys.argv[1], (ROOT / sys.argv[2]).resolve()
for sub in ("characters", "keyframes", "frames", "prompts"):
    (d / sub).mkdir(parents=True, exist_ok=True)
ref = d / "reference.mp4"
ledger = d / "spent.txt"
api.spent, api.LIMIT = float(ledger.read_text()) if ledger.exists() else 0.0, BUDGET
atexit.register(lambda: ledger.write_text(f"{api.spent:.4f}"))  # also on crash / budget stop

# 1. download
if not ref.exists():
    print("⬇️  downloading reference...")
    subprocess.run(["yt-dlp", "-q", "--no-warnings", "-o", str(d / "reference.%(ext)s"), "--write-info-json", "--remux-video", "mp4", url], check=True)

# 2. plan (one API call decides everything); length follows the reference: 10 s base + 8 s extensions
plan_f = d / "plan.json"
if not plan_f.exists():
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ref],
                               capture_output=True, text=True, check=True).stdout)
    n = max(1, min(MAX_PARTS, 1 + round((dur - voice.BASE) / voice.EXT)))
    print(f"🧭 planning: reference {dur:.0f}s → {n} parts, {voice.spans(n)[-1][1]}s...")
    prompt = (TPL / "plan.txt").read_text().replace("{brand}", (TPL / "brand.txt").read_text()).replace("{voices}", (TPL / "voices.txt").read_text()) \
        .replace("{parts}", str(n)).replace("{length}", str(voice.spans(n)[-1][1]))
    plan_f.write_text(gemini("gemini-3.8-flash", [file(ref), {"text": prompt}], responseMimeType="application/json",
                             mediaResolution="MEDIA_RESOLUTION_HIGH")[0]["text"])
plan = json.loads(plan_f.read_text())
spans = voice.spans(len(plan["parts"]))
length = spans[-1][1]
print(f"📋 {plan['title']}: {plan['summary']} · shots {sum(len(s['visuals']) for p in plan['parts'] for s in p['shots'])} (reference {plan['ref_shot_count']})")

# 3. voice first: TTS lines → shot timecodes + packshot start
vo_f = d / "voice.wav"
if not vo_f.exists():
    voice.build(plan, vo_f)
    plan_f.write_text(json.dumps(plan, indent=1))

# 4. music
music = d / "music.mp3"
if not music.exists():
    print("🎵 music...")
    model = "lyria-3-clip-preview" if length <= 30 else "lyria-3-pro-preview"  # clip = 30 s, pro = full song
    music.write_bytes(data(gemini(model, [{"text": f"Instrumental only, no vocals. {plan['music']}"}], responseModalities=["AUDIO"])))

# 5. character from style-only reference frames
refs = []
for t in plan["style_ref_times"]:
    f = d / f"frames/style_{t}.jpg"; refs.append(f)
    if not f.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", ref, "-frames:v", "1", "-vf", "scale=540:-1", f], check=True)
hero = d / "characters/hero.png"
image_with_qa(hero, plan["character_prompt"], refs, required=True)

# 6. keyframes from the character
for k in plan["keyframes"]:
    image_with_qa(d / f"keyframes/{k['name']}.png", k["prompt"], [hero])

# 7. video prompts = timed shots + guards + SFX-only audio
guards = (TPL / "guards.txt").read_text().replace("{character}", plan["character"]).replace("{style}", plan["style"])
def vprompt(i, intro):
    kfs = [k["name"] for k in plan["keyframes"] if k["part"] == i and (d / f"keyframes/{k['name']}.png").exists()]
    refs_line = "REFERENCES: image 1 = the character." + "".join(f" Image {i + 2} = exact keyframe '{n}', match its pose and anatomy." for i, n in enumerate(kfs))
    # a line's time is split evenly across its quick shots
    shots = "\n".join(f"{a + (b - a) * j / len(s['visuals']):.1f}-{a + (b - a) * (j + 1) / len(s['visuals']):.1f}s: {v}"
                      for s in plan["parts"][i]["shots"] for a, b in [s["t"]] for j, v in enumerate(s["visuals"]))
    audio = "Audio: ONLY punchy sound effects on every cut and action. NO music, NO voiceover, NO speech, NO singing."
    (d / f"prompts/part{i}.txt").write_text(f"{intro}\n{refs_line}\n{guards}\n{shots}\n{audio}")
    return [hero] + [d / f"keyframes/{n}.png" for n in kfs]

# 8. base + extensions chained, each QA-gated; every extension returns the full video so far
prev = None
for i, (lo, hi) in enumerate(spans):
    intro = (f"Educational TikTok ad, {hi} seconds, single continuous generation with quick camera cuts at the given timecodes." if i == 0 else
             f"Continue this video for {hi - lo} more seconds with the same character and style, cuts at the given timecodes.")
    video = d / f"part{i}.mp4"
    prev = video_with_qa(video, d / f"prompts/part{i}.txt", vprompt(i, intro), prev=prev, qa_from=max(0, lo - 0.5))

# 9. mix: SFX from the video + music ducked under the voice + voice
mixed = d / "mixed.mp4"
if not mixed.exists():
    # parts where the video model spoke lose their sound effects instead of being regenerated
    mute = "".join(f",volume=enable='between(t,{lo},{hi})':volume=0" for i, (lo, hi) in enumerate(spans) if (d / f"part{i}.speech").exists())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", music, "-i", vo_f, "-filter_complex",
                    f"[2:a]asplit[v][sc];[1:a]atrim=0:{length},afade=t=out:st={length - 1.5}:d=1.5,volume=0.3[m];"
                    f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:release=300[md];[0:a]volume=0.6{mute}[fx];"
                    # voice is already near 0 dBFS: no boost, a limiter keeps the sum from clipping (clipping = crackle)
                    "[fx][md][v]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89:level=false[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", mixed], check=True)

# 10. post: captions from the clean voice track → finish.sh (upscale, 60 fps, packshot, captions)
final = d / "final.mp4"
if not final.exists():
    words_f = d / "voice_words.json"
    # the VO text is known: transcription can drop words (it cut the CTA), so only timing comes from the audio
    lines = [(lo + s["t"][0], lo + s["t"][1], s["vo"]) for p, (lo, _) in zip(plan["parts"], spans) for s in p["shots"]]
    words_f.write_text(json.dumps(align.words_from_script(vo_f, lines)))
    run(ROOT / "finish.sh", mixed, plan["packshot"], final, words_f)

# 11. API review against the reference
report = d / "report.md"
if not report.exists():
    print("🔎 comparing with reference...")
    q = (TPL / "compare.txt").read_text().replace("{plan}", plan_f.read_text())
    report.write_text(gemini("gemini-3.8-flash", [file(ref), file(final), {"text": q}], temperature=0)[0]["text"])
print(f"🏁 {final}\n📝 {report}\n💰 total for this ad ~${api.spent:.2f} of ${BUDGET}")
