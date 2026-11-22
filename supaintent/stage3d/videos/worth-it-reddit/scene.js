// "Is your product worth it?": review/experience prompts cite Reddit in 17.4% of answers (~1 in 6); Google AI Mode cites Reddit in 18.4% of its answers.
// Source: SupaIntent Reddit study, 160,965 AI answers with sources, Aug to Oct 2026.
import { C, anim, ease, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, bar, grow, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/worth-it-reddit/art/${n}.png`;
const RED = "#ff4500";
const type = (o, s, t0, cps = 24) => anim(t => o.update(s.slice(0, Math.max(0, Math.floor((t - t0) * cps))) || " "));

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[1], [0.3, 0.5, -1], [0, 1.2, 0]], [L[4], [0, 0, 0], [0, 0, 0]]]);

// 1. Hook: the question typed into an AI chat
pop(text("SOMEONE JUST ASKED AI", { size: 0.8, y: 6.8, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const ask = card({ w: 7.6, h: 2.0, r: 0.9, y: 4.2, z: 0.3, color: C.ink });
const q = text(" ", { size: 0.48, color: "#ffffff", maxW: 6.8 }); onCard(ask, q, 0, 0); type(q, "Is [your product] worth it?", 0.15);
float(slide(ask, 0, [0, 0, -2], { dur: 0.4 })); leave(ask, L[1] - 0.1, [0, 9, 0]);
const dev = slide(image(art("dev_phone"), { h: 6.2, x: 1.6, y: -5.0 }), 0, [6, 0, 0], { dur: 0.45 }); float(dev, { amp: 0.04 }); leave(dev, L[2], [7, 0, 0]);

// 2. Reddit in ~1 in 6 answers for prompts like that
const rd = card({ w: 1.9, h: 1.9, r: 0.95, y: 5.6, z: 0.4 }); onCard(rd, logo("reddit", { size: 1.25 }));
pop(rd, L[1], { t1: L[2] - 0.1 }); float(rd);
pop(text([["1 IN 6", RED], [" ANSWERS", C.ink]], { size: 0.95, y: 3.9, z: 0.5 }), L[1] + 0.6, { t1: L[2] - 0.1 });
for (let i = 0; i < 6; i++) {
  const c = card({ w: 1.15, h: 1.5, r: 0.18, x: (i - 2.5) * 1.35, y: 2.0, z: 0.2, color: "#ffffff" });
  pop(c, L[1] + 0.8 + i * 0.07, { t1: L[2] - 0.1 });
  if (i === 2) { const hot = card({ w: 1.15, h: 1.5, r: 0.18, x: (i - 2.5) * 1.35, y: 2.0, z: 0.45, color: RED }); pop(hot, at("one"), { t1: L[2] - 0.1 }); }
}

// 3. Google AI Mode: 18% of all its answers
const mode = card({ w: 7.2, h: 5.0, y: 3.4, z: 0.2 });
onCard(mode, logo("google-ai-mode", { size: 1.2 }), -2.4, 1.4);
onCard(mode, text("Google AI Mode", { size: 0.5, align: "left" }), -1.5, 1.4);
const pct = text("0%", { size: 2.0, color: RED }); onCard(mode, pct, 0, -0.3);
anim(t => pct.update(`${Math.round(18 * ease((t - L[2] - 0.4) / 1.2))}%`));
onCard(mode, text("of all its answers cite Reddit", { size: 0.4, weight: 700 }), 0, -1.75);
pop(mode, L[2]); float(mode, { tilt: 0.05 }); leave(mode, L[3] - 0.1, [0, 9, 0]);

// 4. The old complaint thread is your new sales page
const th = card({ w: 7.6, h: 3.6, y: 3.6, z: 0.2 });
onCard(th, logo("reddit", { size: 0.6 }), -3.1, 1.15);
onCard(th, text("r/yourcategory · 2 yrs ago", { size: 0.34, color: C.grey, weight: 600, align: "left" }), -2.6, 1.15);
onCard(th, text("\"Honestly? Not worth it for us.\"", { size: 0.5, align: "left", maxW: 6.8 }), -3.3, 0.1);
onCard(th, text("11 upvotes", { size: 0.36, color: RED, align: "left" }), -3.3, -1.0);
pop(th, L[3]); float(th, { tilt: 0.05 }); leave(th, L[4] - 0.1, [0, 9, 0]);
const stamp = chip("YOUR NEW SALES PAGE", { bg: RED, size: 0.42, y: 1.4, z: 1.0 });
stamp.userData.base.r.z = -0.08; pop(stamp, at("sales") - 0.1, { t1: L[4] - 0.1 });
const wince = slide(image(art("marketer_wince"), { h: 6.2, x: -1.6, y: -5.0 }), L[2], [-6, 0, 0]); float(wince, { amp: 0.04 }); leave(wince, L[4], [-7, 0, 0]);

// 5. CTA
const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.8);
onCard(cta, chip("Reddit Radar", { bg: RED, size: 0.4 }), 0, -0.3);
onCard(cta, text("the threads that shape your answers", { size: 0.34, weight: 700 }), 0, -1.25);
pop(cta, L[4]); float(cta, { tilt: 0.05 });
const ceo = slide(image(art("ceo_point"), { h: 6.2, x: 1.5, y: -5.0 }), L[4], [6, 0, 0]); float(ceo, { amp: 0.04 });

endcard(VO_END + 0.2, "Find the Reddit threads that shape your answers.");
