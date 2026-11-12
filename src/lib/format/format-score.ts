import type { Metric } from "../schema/metric-schema.ts";

/** Human-readable score in the metric's unit: "92.1%", "1,412", "2h 15m", "$3,210". */
export function formatScore(value: number, unit: Metric["unit"]): string {
  const round = (v: number, digits: number) => Number(v.toFixed(digits)).toLocaleString("en-US");
  switch (unit) {
    case "percent":
      return `${round(value, Math.abs(value) < 10 ? 2 : 1)}%`;
    case "elo":
      return round(value, 0);
    case "dollars":
      return `$${round(value, 0)}`;
    case "minutes": {
      if (Math.abs(value) < 60) return `${round(value, 1)} min`;
      const h = Math.floor(value / 60);
      const m = Math.round(value % 60);
      return m ? `${h}h ${m}m` : `${h}h`;
    }
    default:
      return round(value, Math.abs(value) < 10 ? 3 : 1);
  }
}
