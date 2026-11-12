import type { Metric } from "../schema/metric-schema.ts";
import type { Score } from "../schema/score-schema.ts";

/** The running best result: each row is a new record at the time it was set. */
export function bestOverTime(rows: Score[], metric: Metric): Score[] {
  const better = (a: number, b: number) => (metric.direction === "higher" ? a > b : a < b);
  const sorted = [...rows].sort((a, b) => a.date.localeCompare(b.date) || (better(a.score, b.score) ? -1 : 1));
  const records: Score[] = [];
  for (const row of sorted) {
    const last = records.at(-1);
    if (!last || better(row.score, last.score)) records.push(row);
  }
  return records;
}
