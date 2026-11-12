import type { Benchmark } from "../schema/benchmark-schema.ts";
import type { Score } from "../schema/score-schema.ts";
import { formatScore } from "../format/format-score.ts";
import { headlineRows } from "./headline-rows.ts";
import { monthsBetween } from "./months-between.ts";
import { metricFloor } from "./progress.ts";
import type { Saturation } from "./saturation-types.ts";
import { SATURATION_RULES as R } from "./saturation-rules.ts";
import { summarizeResults } from "./summarize-results.ts";

/** Decides whether a benchmark still separates the best models, and says why in one line. */
export function computeSaturation(benchmark: Benchmark, allRows: Score[], today: string): Saturation {
  const { metric } = benchmark;
  const rows = headlineRows(benchmark, allRows);
  const summary = summarizeResults(rows, metric);
  const facts = { rows, best: summary?.best, progress: summary?.progress, spread: summary?.spread, yearGain: summary?.yearGain };

  if (benchmark.status_override) {
    return { ...facts, status: benchmark.status_override.status, reason: benchmark.status_override.reason };
  }
  if (!summary) return { ...facts, status: "unknown", reason: "No scores recorded yet." };

  const { best, spread, yearGain, latestDate } = summary;
  const pts = (v: number) => formatScore(v, metric.unit).replace("%", " pts");
  const parts = [`Best ${formatScore(best.score, metric.unit)} (${best.date.slice(0, 7)})`];
  if (metric.ceiling) parts.push(`ceiling ${formatScore(metric.ceiling.value, metric.unit)}`);
  if (spread !== undefined) parts.push(`top 5 within ${pts(spread)}`);
  if (yearGain !== undefined) parts.push(`+${pts(yearGain)} in a year`);
  const reason = parts.join(" · ");

  if (summary.progress === undefined || !metric.ceiling) {
    return { ...facts, status: "headroom", reason: `${reason} · open-ended metric` };
  }
  const p = summary.progress;
  const gap = Math.abs(metric.ceiling.value - metricFloor(metric));
  const tight = spread !== undefined && gap > 0 && spread / gap <= R.tightSpread;
  if (p >= R.saturatedAt || (p >= R.saturatedIfTightAt && tight)) return { ...facts, status: "saturated", reason };

  if (monthsBetween(latestDate, today) > R.staleAfterMonths) {
    return { ...facts, status: "unknown", reason: `No scores since ${latestDate.slice(0, 7)} · ${reason}` };
  }
  const perMonth = yearGain !== undefined && gap > 0 ? yearGain / gap / 12 : 0;
  const monthsLeft = perMonth > 0 ? (R.saturatedAt - p) / perMonth : Infinity;
  if (p >= R.approachingAt || monthsLeft <= R.approachingWithinMonths) return { ...facts, status: "approaching", reason };
  return { ...facts, status: "headroom", reason };
}
