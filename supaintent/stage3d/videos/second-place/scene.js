// "Every AI agrees on #1, they split on #2": e-commerce site search. Algolia leads everywhere; #2 is Constructor (ChatGPT, AI Mode), Bloomreach (Gemini), Elastic (Perplexity).
// Source: SupaIntent e-commerce site search report (93 tracked answers, 2026).
import { C, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, crown, bar, grow, pop, slide, flip, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/second-place/art/${n}.png`;

cameraKeys([[0, [0, 0.4, -0.6], [0, 1.6, 0]], [L[2], [0, 0.6, -1], [0, 2, 0]], [L[3], [0, 0, 0], [0, 0, 0]]]);

// 1. Podium: Algolia #1 in every AI
pop(text([["EVERY AI AGREES\n", C.ink], ["#1 = ALGOLIA", C.acc]], { size: 0.85, y: 6.6, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const pod = [[-2.6, 1.6, "2", "#cbd5e1"], [0, 2.6, "1", C.acc], [2.6, 1.0, "3", "#e2e8f0"]];
for (const [x, h, n, color] of pod) {
  const b = grow(bar({ w: 2.4, h, d: 1.4, color, x, y: -0.6, z: 0 }), 0.1 + +n * 0.12, { dur: 0.6 }); leave(b, L[2] - 0.1, [0, -10, 0]);
  const lb = text(n, { size: 0.8, color: n === "1" ? "#ffffff" : C.grey, x, y: -0.6 + h / 2, z: 0.8 }); pop(lb, 0.5 + +n * 0.1); leave(lb, L[2] - 0.1, [0, -10, 0]);
}
const lead = chip("Algolia", { bg: C.ink, size: 0.42, y: 2.6, z: 0.4 }); pop(lead, at("Algolia") - 0.1); float(lead); leave(lead, L[2] - 0.1, [0, -10, 0]);
const cr = crown({ s: 0.45, y: 3.55, z: 0.4 }); pop(flip(cr, at("Algolia"), { turns: 1 }), at("Algolia")); float(cr, { phase: 1 }); leave(cr, L[2] - 0.1, [0, -10, 0]);
const q = chip("?", { bg: C.red, size: 0.55, x: -2.6, y: 1.6, z: 0.5 }); pop(flip(q, L[1], { turns: 2, dur: 0.8 }), L[1]); leave(q, L[2] - 0.1, [0, -10, 0]);
const cheer = slide(image(art("ceo_cheer"), { h: 6.2, x: 1.9, y: -5.0, z: 1.5 }), 0, [6, 0, 0], { dur: 0.45 }); float(cheer, { amp: 0.04 }); leave(cheer, L[1], [7, 0, 0]);
const think = slide(image(art("marketer_think"), { h: 6.2, x: -1.9, y: -5.0, z: 1.5 }), L[1], [-6, 0, 0]); float(think, { amp: 0.04 }); leave(think, L[3], [-7, 0, 0]);

// 2-3. #2 by engine
pop(text([["#2? ", C.red], ["THEY SPLIT", C.ink]], { size: 0.95, y: 6.6, z: 0.5 }), L[1], { t1: L[3] - 0.1 });
const rows = [["chatgpt", "Constructor", "ChatGPT"], ["google-ai-mode", "Constructor", "Google"], ["gemini", "Bloomreach", "Gemini"], ["perplexity", "Elastic", "Perplexity"]];
rows.forEach(([lg, brand, word], i) => {
  const t0 = at(word) - 0.1, y = 4.9 - i * 1.25;
  const row = card({ w: 7.6, h: 1.05, r: 0.5, y, z: 1.6 });
  onCard(row, logo(lg, { size: 0.7 }), -3.1, 0);
  onCard(row, text("#2", { size: 0.42, color: C.grey }), -1.9, 0);
  onCard(row, chip(brand, { bg: C.acc, size: 0.36 }), 1.4, 0);
  slide(row, t0, [9, 0, 0], { dur: 0.35 }); float(row, { amp: 0.03, phase: i }); leave(row, L[3] - 0.1, [-10, 0, 0]);
});

// 4. Second place is still open
pop(text([["2ND PLACE\n", C.ink], ["IS UP FOR GRABS", C.acc]], { size: 0.95, y: 5.2, z: 0.5 }), L[3], { t1: L[4] - 0.1 });
const run = image(art("marketer_run"), { h: 6.2, x: 0, y: -5.0 });
slide(run, L[3], [-8, 0, 0], { dur: 0.9 }); float(run, { amp: 0.06, speed: 6 }); leave(run, L[4], [8, 0, 0]);
const two = card({ w: 2.2, h: 2.2, r: 1.1, y: 2.0, z: 0.4, color: C.gold }); onCard(two, text("2", { size: 1.3, color: "#ffffff" }));
pop(flip(two, L[3] + 0.3, { turns: 2, dur: 1 }), L[3] + 0.3, { t1: L[4] - 0.1 });

// 5. CTA
const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.85);
onCard(cta, text("your position in every AI", { size: 0.4, weight: 700 }), 0, -0.2);
["chatgpt", "gemini", "google-ai-mode", "perplexity"].forEach((n, i) => onCard(cta, logo(n, { size: 0.62 }), (i - 1.5) * 1.2, -1.2));
pop(cta, L[4]); float(cta, { tilt: 0.05 });
const cheer2 = slide(image(art("ceo_cheer"), { h: 6.2, x: -1.4, y: -5.0 }), L[4], [-6, 0, 0]); float(cheer2, { amp: 0.04 });

endcard(VO_END + 0.2, "Check your rank in every AI.");
