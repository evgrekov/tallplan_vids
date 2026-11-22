// "X vs Y, according to AI" series: overall duel, then one duel per topic with a crown, recap of winners, CTA.
// Each video's scene.js only passes its brands and DUELS: [line, TOPIC, A %, B %, art]; data from brand-comparisons.json.
import { C, anim, at, LINES as L, VO_END, text, image, card, onCard, logo, chip, crown, bar, grow, pop, slide, float, leave, cameraKeys, endcard, lockup } from "/web/engine.js";

export function versus(id, A, B, DUELS, { answers = 80, hook = "marketer_scales", end = "marketer_point" } = {}) {
  const art = n => `/videos/${id}/art/${n}.png`;
  const BASE = 1.6, MAXH = 3.0;  // bars stand on y = BASE, 100% = MAXH units
  const last = DUELS.length + 1;  // line index of "AI doesn't crown one winner"

  cameraKeys([[0, [0, 0, 0], [0, 0, 0]], [L[1], [0, 0, -0.4], [0, 0, 0]], [L[last], [0, 0, 0], [0, 0, 0]]]);

  // 1. Hook: two brand cards face off, N answers from two AIs
  pop(text([[A.name.toUpperCase(), A.color], [" vs ", C.grey], [B.name.toUpperCase(), B.color]], { size: 1.0, y: 6.7, z: 0.5 }), -0.3, { t1: L[1] - 0.1 });
  [A, B].forEach((br, i) => {
    const c = card({ w: 3.8, h: 2.2, x: i ? 2.05 : -2.05, y: 4.4, z: 0.3, color: br.color });
    onCard(c, text(br.name, { size: 0.62, color: "#ffffff", maxW: 3.4 }), 0, 0);
    slide(pop(c, 0.1 + i * 0.15), 0.1 + i * 0.15, [i ? 6 : -6, 0, 0]); float(c, { phase: i }); leave(c, L[1] - 0.1, [i ? 9 : -9, 0, 0]);
  });
  ["chatgpt", "gemini"].forEach((n, i) => {
    const c = card({ w: 1.3, h: 1.3, r: 0.65, x: i ? 0.9 : -0.9, y: 2.4, z: 0.4 }); onCard(c, logo(n, { size: 0.8 }));
    pop(c, at("ChatGPT") - 0.1 + i * 0.3, { t1: L[1] - 0.1 }); float(c, { phase: i + 2 });
  });
  pop(chip(`${answers} answers`, { bg: C.ink, size: 0.34, y: 1.2, z: 0.5 }), at("answers") - 0.4, { t1: L[1] - 0.1 });
  const h = slide(image(art(hook), { h: 6.4, x: 0, y: -4.8 }), 0, [0, -6, 0], { dur: 0.45 }); float(h, { amp: 0.04 }); leave(h, L[2], [0, -8, 0]);

  // 2+. One duel per line: topic, two growing bars with counting labels, crown on the winner (tie chip on the overall line)
  DUELS.forEach(([li, topic, a, b, who], k) => {
    const t0 = L[li], t1 = L[li + 1] - 0.1;
    pop(text(topic, { size: 0.95, y: 6.8, z: 0.5, maxW: 8.2 }), t0, { t1 });
    [[A, a, -1.8], [B, b, 1.8]].forEach(([br, v, x], j) => {
      const b3 = bar({ w: 2.0, h: Math.max(MAXH * v / 100, 0.02), d: 1.0, color: br.color, x, y: BASE, z: 0 });
      grow(b3, t0 + 0.3 + j * 0.15, { dur: 0.9 }); leave(b3, t1, [0, 9, 0]);
      const lab = text("0%", { size: 0.75, color: br.color, x, y: BASE + MAXH * v / 100 + 0.6, z: 0.7 });
      anim(t => lab.update(`${Math.round(v * Math.min(Math.max((t - t0 - 0.3 - j * 0.15) / 0.9, 0), 1))}%`));
      pop(lab, t0 + 0.3 + j * 0.15, { t1 });
      pop(chip(br.name, { bg: br.color, size: 0.34, x, y: BASE - 0.55, z: 0.6 }), t0 + 0.1, { t1 });
    });
    if (k) pop(crown({ s: 0.45, x: a > b ? -1.8 : 1.8, y: BASE + MAXH * Math.max(a, b) / 100 + 1.45, z: 0.6 }), t0 + 1.3, { t1 });
    else pop(chip(Math.abs(a - b) <= 5 ? "ALMOST A TIE" : "CLOSE CALL", { bg: C.gold, fg: C.ink, size: 0.36, y: 6.0, z: 0.6 }), t0 + 1.2, { t1 });
    if (k) { const p = slide(image(art(who), { h: 6.4, x: k % 2 ? 1.6 : -1.6, y: -4.8 }), t0, [k % 2 ? 6 : -6, 0, 0]); float(p, { amp: 0.04 }); leave(p, t1 + 0.1, [k % 2 ? 7 : -7, 0, 0]); }
  });

  // Recap: one winner per question, then CTA
  const see = at("See", -1);
  pop(text([["ONE WINNER\n", C.ink], ["PER QUESTION", C.acc]], { size: 0.95, y: 6.4, z: 0.5 }), L[last], { t1: see - 0.1 });
  DUELS.slice(1).forEach(([, topic, a, b], i) => {
    const br = a > b ? A : B, c = card({ w: 7.0, h: 1.0, r: 0.5, y: 4.2 - i * 1.3, z: 0.3 });
    onCard(c, text(topic[0] + topic.slice(1).toLowerCase(), { size: 0.4, weight: 700, align: "left", maxW: 4.2 }), -3.1, 0);
    onCard(c, chip(br.name, { bg: br.color, size: 0.32 }), 2.2, 0);
    pop(c, L[last] + 0.2 + i * 0.15, { t1: see - 0.1 }); float(c, { phase: i, amp: 0.03 });
  });
  const cta = card({ w: 7.4, h: 3.6, y: 3.2, z: 0.4 });
  onCard(cta, lockup({ size: 0.6 }), 0, 0.8);
  onCard(cta, text("What does AI say about your brand?", { size: 0.38, weight: 700 }), 0, -0.3);
  ["chatgpt", "gemini", "google-ai-mode"].forEach((n, i) => onCard(cta, logo(n, { size: 0.7 }), (i - 1) * 1.1, -1.2));
  pop(cta, see); float(cta, { tilt: 0.05 });
  const e = slide(image(art(end), { h: 6.4, x: -1.4, y: -4.8 }), L[last], [-6, 0, 0]); float(e, { amp: 0.04 });

  endcard(VO_END + 0.2, "See what AI says about your brand.");
  return Math.ceil(VO_END + 3);
}
