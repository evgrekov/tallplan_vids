// "Stripe vs PayPal, according to AI": near tie overall, but a different winner per topic.
// Source: SupaIntent public brand comparison stripe-vs-paypal (80 analyzed answers, ChatGPT + Gemini, 2026-08-30 and 2026-09-06):
// visibility total 85/80, checkout conversion 20/91, developer integration 83/23, recurring payments 79/0 (Stripe/PayPal, %).
// Series template: copy the folder, change DUELS + script.json for another pair from brand-comparisons.json.
import { C, anim, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, crown, bar, grow, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export const LENGTH = Math.ceil(VO_END + 3);
const art = n => `/videos/stripe-vs-paypal/art/${n}.png`;
const A = { name: "Stripe", color: "#635bff" }, B = { name: "PayPal", color: "#003087" };
const DUELS = [  // [line, topic, Stripe %, PayPal %, character]
  [1, "OVERALL", 85, 80, "marketer_scales"],
  [2, "CHECKOUT", 20, 91, "ceo_paying"],
  [3, "DEVELOPERS", 83, 23, "dev_confident"],
  [4, "SUBSCRIPTIONS", 79, 0, "marketer_point"],
];
const BASE = 1.6, MAXH = 3.0;  // bars stand on y = BASE, 100% = MAXH units

cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[1], [0, 0, -0.4], [0, 0, 0]], [L[5], [0, 0, 0], [0, 0, 0]]]);

// 1. Hook: two brand cards face off, 80 answers from two AIs
pop(text([["STRIPE", A.color], [" vs ", C.grey], ["PAYPAL", B.color]], { size: 1.0, y: 6.7, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
[A, B].forEach((br, i) => {
  const c = card({ w: 3.6, h: 2.2, x: i ? 2.0 : -2.0, y: 4.4, z: 0.3, color: br.color });
  onCard(c, text(br.name, { size: 0.7, color: "#ffffff" }), 0, 0);
  slide(pop(c, 0.1 + i * 0.15), 0.1 + i * 0.15, [i ? 6 : -6, 0, 0]); float(c, { phase: i }); leave(c, L[1] - 0.1, [i ? 9 : -9, 0, 0]);
});
["chatgpt", "gemini"].forEach((n, i) => {
  const c = card({ w: 1.3, h: 1.3, r: 0.65, x: i ? 0.9 : -0.9, y: 2.4, z: 0.4 }); onCard(c, logo(n, { size: 0.8 }));
  pop(c, at("ChatGPT") - 0.1 + i * 0.3, { t1: L[1] - 0.1 }); float(c, { phase: i + 2 });
});
pop(chip("80 answers", { bg: C.ink, size: 0.34, y: 1.2, z: 0.5 }), at("eighty") - 0.1, { t1: L[1] - 0.1 });
const hook = slide(image(art("marketer_scales"), { h: 6.4, x: 0, y: -4.8 }), 0, [0, -6, 0], { dur: 0.45 }); float(hook, { amp: 0.04 }); leave(hook, L[1], [0, -8, 0]);

// 2-5. One duel per line: topic, two growing bars with counting labels, crown on the winner
DUELS.forEach(([li, topic, a, b, who], k) => {
  const t0 = L[li], t1 = L[li + 1] - 0.1;
  pop(text(topic, { size: 0.95, y: 6.8, z: 0.5 }), t0, { t1 });
  [[A, a, -1.8], [B, b, 1.8]].forEach(([br, v, x], j) => {
    const b3 = bar({ w: 2.0, h: Math.max(MAXH * v / 100, 0.02), d: 1.0, color: br.color, x, y: BASE, z: 0 });
    grow(b3, t0 + 0.3 + j * 0.15, { dur: 0.9 }); leave(b3, t1, [0, 9, 0]);
    const lab = text("0%", { size: 0.75, color: br.color, x, y: BASE + MAXH * v / 100 + 0.6, z: 0.7 });
    anim(t => lab.update(`${Math.round(v * Math.min(Math.max((t - t0 - 0.3 - j * 0.15) / 0.9, 0), 1))}%`));
    pop(lab, t0 + 0.3 + j * 0.15, { t1 });
    pop(chip(br.name, { bg: br.color, size: 0.34, x, y: BASE - 0.55, z: 0.6 }), t0 + 0.1, { t1 });
  });
  if (Math.abs(a - b) >= 10) pop(crown({ s: 0.45, x: a > b ? -1.8 : 1.8, y: BASE + MAXH * Math.max(a, b) / 100 + 1.45, z: 0.6 }), t0 + 1.3, { t1 });
  else pop(chip("ALMOST A TIE", { bg: C.gold, fg: C.ink, size: 0.36, y: 5.6, z: 0.6 }), t0 + 1.2, { t1 });
  if (k) { const p = slide(image(art(who), { h: 6.4, x: k % 2 ? 1.6 : -1.6, y: -4.8 }), t0, [k % 2 ? 6 : -6, 0, 0]); float(p, { amp: 0.04 }); leave(p, t1 + 0.1, [k % 2 ? 7 : -7, 0, 0]); }
});
const tie = slide(image(art("marketer_scales"), { h: 6.4, x: 0, y: -4.8 }), L[1], [0, -6, 0]); float(tie, { amp: 0.04 }); leave(tie, L[2], [0, -8, 0]);

// 6. One winner per question, then CTA
const see = at("See", -1);
pop(text([["ONE WINNER\n", C.ink], ["PER QUESTION", C.acc]], { size: 0.95, y: 6.4, z: 0.5 }), L[5], { t1: see - 0.1 });
[["Checkout", B], ["Developers", A], ["Subscriptions", A]].forEach(([tp, br], i) => {
  const c = card({ w: 7.0, h: 1.0, r: 0.5, y: 4.2 - i * 1.3, z: 0.3 });
  onCard(c, text(tp, { size: 0.4, weight: 700, align: "left" }), -3.1, 0);
  onCard(c, chip(br.name, { bg: br.color, size: 0.32 }), 2.2, 0);
  pop(c, L[5] + 0.2 + i * 0.15, { t1: see - 0.1 }); float(c, { phase: i, amp: 0.03 });
});
const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
onCard(cta, lockup({ size: 0.6 }), 0, 0.8);
onCard(cta, text("What does AI say about your brand?", { size: 0.38, weight: 700 }), 0, -0.3);
["chatgpt", "gemini", "google-ai-mode"].forEach((n, i) => onCard(cta, logo(n, { size: 0.7 }), (i - 1) * 1.1, -1.2));
pop(cta, see); float(cta, { tilt: 0.05 });
const end = slide(image(art("marketer_point"), { h: 6.4, x: -1.4, y: -4.8 }), L[5], [-6, 0, 0]); float(end, { amp: 0.04 });

endcard(VO_END + 0.2, "See what AI says about your brand.");
