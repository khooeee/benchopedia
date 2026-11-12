import type { Metric } from "../schema/metric-schema.ts";
import type { Score } from "../schema/score-schema.ts";
import { bestOverTime } from "./best-over-time.ts";
import { monthsBetween } from "./months-between.ts";
import { progress } from "./progress.ts";

export type ResultSummary = {
  best: Score;
  progress?: number;
  /** #1 minus #5 distinct models within a year of the best result, in metric units. */
  spread?: number;
  /** Improvement of the best result over the 12 months before it, in metric units. */
  yearGain?: number;
  latestDate: string;
};

/** The numbers saturation is judged on. Returns undefined when there are no rows. */
export function summarizeResults(rows: Score[], metric: Metric): ResultSummary | undefined {
  const records = bestOverTime(rows, metric);
  const best = records.at(-1);
  if (!best) return undefined;
  const higher = metric.direction === "higher";

  const perModel = new Map<string, number>();
  for (const r of rows) {
    if (monthsBetween(r.date, best.date) > 12) continue;
    const prev = perModel.get(r.model);
    if (prev === undefined || (higher ? r.score > prev : r.score < prev)) perModel.set(r.model, r.score);
  }
  const top = [...perModel.values()].sort((a, b) => (higher ? b - a : a - b)).slice(0, 5);
  const spread = top.length === 5 ? Math.abs(top[0] - top[4]) : undefined;

  const yearAgo = records.filter((r) => monthsBetween(r.date, best.date) >= 12).at(-1);
  const yearGain = yearAgo ? Math.abs(best.score - yearAgo.score) : undefined;
  const latestDate = rows.reduce((d, r) => (r.date > d ? r.date : d), "");
  return { best, progress: progress(best.score, metric), spread, yearGain, latestDate };
}
