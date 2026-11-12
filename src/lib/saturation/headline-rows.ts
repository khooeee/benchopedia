import type { Benchmark } from "../schema/benchmark-schema.ts";
import type { Score } from "../schema/score-schema.ts";

/**
 * Rows that count toward saturation: the headline metric only, and only the newest
 * benchmark version that has any results. Unversioned rows count for every version.
 */
export function headlineRows(benchmark: Benchmark, rows: Score[]): Score[] {
  const headline = rows.filter((r) => !r.metric);
  const scored = new Set(headline.map((r) => r.version).filter(Boolean));
  const latest = [...benchmark.versions].reverse().find((v) => scored.has(v.version))?.version;
  return latest ? headline.filter((r) => !r.version || r.version === latest) : headline;
}
