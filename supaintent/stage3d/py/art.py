# /// script
# dependencies = []
# ///
"""Illustration cutouts for the 3D stage (gpt-image, transparent PNG). Style ref is made once; every cutout is an edit from it.
Usage: uv run py/art.py <video_dir>   (reads <video_dir>/art.json: {name: prompt})"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import oai

ROOT = pathlib.Path(__file__).parent.parent
STYLE = ("Flat editorial vector illustration for a serious business publication: simple adult characters with realistic proportions, "
         "minimal faces (small dot eyes, short brows, no big cartoon eyes), clean geometric shapes with subtle two-tone shading, "
         "muted palette of deep navy, charcoal, slate grey, warm skin tones and a single accent of blue #2563eb. "
         "Grown-up and witty, like a Wall Street Journal or Economist explainer. Not childish, not cute, not chibi, not anime, not 3D, no outlines, no text.")
REF = ROOT / "assets/style_ref.png"

if not REF.exists():
    oai.image(f"{STYLE} Character lineup on a transparent background: a male CEO around 55 with short silver hair in a navy suit and blue tie; "
              "a female marketing lead around 38 with a dark low ponytail in a charcoal blazer; a male developer around 30 with short dark hair, "
              "glasses and a grey hoodie. Full figures standing side by side, facing the viewer, neutral poses.", REF, quality="high", size="1536x1024", background="transparent")
    print(f"🎨 style ref  ${oai.spent:.3f}")

if len(sys.argv) > 1:
    d = pathlib.Path(sys.argv[1]); (d / "art").mkdir(exist_ok=True)
    for name, prompt in json.loads((d / "art.json").read_text()).items():
        out = d / "art" / f"{name}.png"
        if out.exists(): continue
        oai.edit(f"{STYLE} Same characters and style as the reference. {prompt} Isolated on a fully transparent background, no floor, no shadow, no text.",
                 [REF], out, quality="medium", background="transparent")
        print(f"🖼️  {name}  ${oai.spent:.3f}")
