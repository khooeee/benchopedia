import type { Catalog, Problem } from "../catalog/catalog-types.ts";

/** The same result from the same source must not be recorded twice. */
export function checkDuplicateScores(catalog: Catalog): Problem[] {
  const problems: Problem[] = [];
  for (const [benchmarkId, rows] of Object.entries(catalog.scores)) {
    const seen = new Map<string, number>();
    rows.forEach((row, i) => {
      const key = JSON.stringify([row.model, row.version, row.metric, row.setting, row.source, row.score]);
      const first = seen.get(key);
      if (first !== undefined) {
        problems.push({ level: "error", file: `scores/${benchmarkId}.yaml #${i + 1}`, message: `duplicate of row #${first + 1}` });
      } else {
        seen.set(key, i);
      }
    });
  }
  return problems;
}
