// "The most important page about your brand isn't on your website": G2 reviews page (48% of G2 citations) and category rankings (19%).
// Source: SupaIntent review sites study, 167,514 AI answers, Aug to Nov 2026.
import { C, anim, ease, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, star, bar, grow, pop, slide, flip, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/g2-pages/art/${n}.png`;

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[2], [0.3, 0.6, -1.2], [0, 1, 0]], [L[4], [0, 0, 0], [0, 0, 0]]]);

// 1. Hook: your website card gets crossed out
pop(text("THE #1 PAGE\nABOUT YOUR BRAND", { size: 0.95, y: 6.1, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
const site = card({ w: 6.4, h: 3.6, y: 2.2, z: 0.3 });
onCard(site, text("yourbrand.com", { size: 0.42, color: C.grey, weight: 700 }), 0, 1.2);
[[-0.2, 3.6], [-0.75, 4.6], [-1.3, 2.8]].forEach(([y, w]) => onCard(site, card({ w, h: 0.28, r: 0.14, color: "#dbe1ec", depth: 0.02 }), 0, y));
float(slide(site, 0, [0, -1.2, -2], { dur: 0.6 }), { tilt: 0.06 });
leave(site, L[1] - 0.15, [-9, 0, 0]);
const nope = chip("NOT YOUR WEBSITE", { bg: C.red, size: 0.42, y: 2.2, z: 1.2 });
nope.rotation.z = 0.12; nope.userData.base.r.z = 0.12; pop(nope, at("isn't"), { t1: L[1] - 0.15 });
const lap = slide(image(art("marketer_laptop"), { h: 6.4, x: -1.8, y: -4.8 }), 0, [-6, 0, 0], { dur: 0.45 });
float(lap, { amp: 0.04 }); leave(lap, L[4], [-7, 0, 0]);

// 2. It's your G2 reviews page
const g2 = card({ w: 6, h: 4.4, y: 2.6, z: 0.3 });
onCard(g2, logo("g2", { size: 1.6 }), 0, 0.85);
onCard(g2, text("Reviews page", { size: 0.62 }), 0, -0.6);
[-1.2, -0.6, 0, 0.6, 1.2].forEach(x => onCard(g2, star({ s: 0.24 }), x, -1.5));
pop(flip(g2, L[1], { turns: 1, dur: 0.7 }), L[1]); float(g2, { tilt: 0.05 }); leave(g2, L[2] - 0.1, [0, 9, 0]);
const ceo = slide(image(art("ceo_surprised"), { h: 6.4, x: 1.9, y: -4.8, z: 0.1 }), L[1] + 0.2, [7, 0, 0]);
float(ceo, { amp: 0.04, phase: 2 }); leave(ceo, L[4], [7, 0, 0]);

// 3-4. Where AI's G2 links go: bars
pop(text("WHERE AI'S G2 LINKS GO", { size: 0.62, y: 6.9, z: 0.4 }), L[2], { t1: L[4] - 0.1 });
const bars = [["Reviews\npages", 48, C.acc, -1.7, at("half")], ["Category\nrankings", 19, "#94a3b8", 1.7, at("nineteen")]];
for (const [label, v, color, x, t0] of bars) {
  const b = grow(bar({ w: 2.2, h: v * 0.09, d: 1.2, color, x, y: 0.4, z: 0.2 }), t0); leave(b, L[4] - 0.1, [0, -9, 0]);
  const n = text("0%", { size: 1.0, color, x, y: 0.4 + v * 0.09 + 0.75, z: 0.9 });
  pop(n, t0); leave(n, L[4] - 0.1, [0, -9, 0]);
  anim(t => n.update(`${Math.round(v * ease((t - t0) / 0.8))}%`));
  const lb = text(label, { size: 0.4, weight: 700, color: C.ink, x, y: -0.2, z: 0.9 }); pop(lb, t0); leave(lb, L[4] - 0.1, [0, -9, 0]);
}

// 5. You own neither + CTA
pop(text([["YOU OWN ", C.ink], ["NEITHER", C.red]], { size: 0.95, y: 6.6, z: 0.4 }), L[4]);
const shrug = slide(image(art("marketer_shrug"), { h: 6.4, x: 0, y: -4.8 }), L[4], [0, -4, 0]); float(shrug, { amp: 0.04 });
const cta = card({ w: 7.4, h: 3.8, y: 2.6, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.9);
onCard(cta, chip("Review Radar", { bg: C.acc, size: 0.38 }), 0, -0.1);
["g2", "capterra", "trustpilot"].forEach((n, i) => onCard(cta, logo(n, { size: 0.75 }), (i - 1) * 1.5, -1.25));
pop(cta, at("See", -1) - 0.1); float(cta, { tilt: 0.05 });

endcard(VO_END + 0.2, "See which review pages shape your category.");
