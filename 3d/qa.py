"""QA gate: gemini-3.8-flash checks a generated clip before we spend more. Only creepy defects block: wrong clothes, extra
people or off-script poses are fine for a TikTok ad. A failure counts only when a second, skeptical pass confirms it.
Speech in the clip doesn't block: it prints speech=1 and the mix mutes that part's sound effects.
Usage: python3 qa.py <video.mp4|image.png> [--from SEC]   → exit 0 = PASS, 1 = FAIL
"""
import argparse, json, pathlib, subprocess, tempfile
import api
from api import gemini, file

HARD = {
    "no_text": "NO words, sentences, subtitles or UI drawn anywhere (graphic numbers/counters, glows, arrows and ruler ticks are fine).",
    "audio": "The audio has ONLY sound effects: no speech, voiceover, singing or music.",
    "face": "No horror: faces never turn into realistic, creepy skulls. Cartoon-style x-ray, skeleton or anatomy overlays are fine.",
    "anatomy": "No reversed or twisted joints, no extra or missing limbs, no melted or merged bodies, nothing (spine, bones, organs) sticking out through the body outline; cartoon x-ray drawn inside the body is fine.",
    "artifacts": "No creepy glitches: melting or distorted faces, half-transparent ghost figures, garbled smeared shapes.",
}

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--from", dest="start", type=float, default=0)
a = ap.parse_args()

image = a.video.endswith(".png")
hard = {k: v for k, v in HARD.items() if not (image and k in ("no_text", "audio"))}
if image:
    media, stills = [file(a.video)], []
else:
    tmp = pathlib.Path(tempfile.mkdtemp())
    # re-encode the cut: stream copy starts at the previous keyframe and drags already-approved parts into the check
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", a.video, "-c:v", "libx264", "-crf", "20", "-c:a", "aac", tmp / "qa.mp4"], check=True)
    # video sampling is too coarse for joints → also send full-res stills every 0.5 s
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp / "qa.mp4", "-vf", "fps=2", tmp / "f%03d.png"], check=True)
    media = [file(tmp / "qa.mp4")]
    stills = [p for i, f in enumerate(sorted(tmp.glob("f*.png"))) for p in ({"text": f"Still at {i / 2:.1f}s:"}, file(f))]

def ask(prompt, checks):
    return json.loads(gemini("gemini-3.8-flash", [*media, *stills, {"text": f"{prompt} Checks: {json.dumps(checks)}. "
                             "Return ONLY JSON: {\"<check>\": {\"pass\": bool, \"why\": str}}"}],
                             responseMimeType="application/json", temperature=0, mediaResolution="MEDIA_RESOLUTION_HIGH")[0]["text"])

kind = "image" if image else "video (times in seconds from the clip start)"
res = ask(f"QA this generated ad {kind}. For each check answer pass true/false with a short reason and the time of any failure. "
          "Judge anatomy and faces frame by frame on the attached stills. Minor imperfections are fine; fail only what a viewer "
          "would find broken or creepy.", hard)
failed = {k: hard[k] for k in hard if not res[k]["pass"]}
if failed:  # first pass hallucinates (ruler ticks read as text, wrong timecodes): confirm before paying for a regeneration
    claims = {k: f"{v} — first reviewer claimed: {res[k]['why']}" for k, v in failed.items()}
    again = ask(f"Second opinion on this {kind}. A first reviewer flagged the checks below. Be skeptical: fail a check only if the defect "
                "is clearly visible on the stills (or clearly audible) right now; otherwise pass it.", claims)
    for k in failed:
        res[k] = again[k] if not again[k]["pass"] else res[k] | {"why": f"{res[k]['why']} (rejected on recheck: {again[k]['why']})", "pass": True}
for k, v in res.items():
    print(f"{'✅' if v['pass'] else '❌'} {k}: {v['why']}")
speech = int("audio" in res and not res["audio"]["pass"])  # fixed in the mix by muting, not worth a regeneration
fails = sum(not v["pass"] for k, v in res.items() if k != "audio")
print(f"{'🟢 PASS' if not fails else '🔴 FAIL'} · fails={fails} · speech={speech} · 💰 ~${api.spent:.4f}")
raise SystemExit(1 if fails else 0)
