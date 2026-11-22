// Tesla vs Hyundai. Source: SupaIntent brand comparison tesla-vs-hyundai (80 answers, ChatGPT + Gemini, 2026-08-30 and 09-06), visibility %; crowns only on topics where the leader's mentions are mostly positive.
import { versus } from "/web/versus.js";
export const LENGTH = versus("tesla-vs-hyundai", { name: "Tesla", color: "#cc0000" }, { name: "Hyundai", color: "#002c5f" }, [
  [1, "OVERALL", 81, 76, "marketer_scales"],
  [2, "CHARGING NETWORK", 90, 6, "marketer_surprised"],
  [3, "IN-CAR CHARGING", 4, 80, "ceo_magnifier"],
  [4, "EFFICIENCY", 56, 9, "dev_confident"],
]);
