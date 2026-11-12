import type { Catalog, Problem } from "../catalog/catalog-types.ts";
import { metricRange } from "../saturation/metric-range.ts";

/** Scores, ceilings and dates must be physically possible. */
export function checkValues(catalog: Catalog, today: string): Problem[] {
  const problems: Problem[] = [];
  const models = new Map(catalog.models.map((m) => [m.id, m]));

  for (const b of catalog.benchmarks) {
    const file = catalog.files.get(b) ?? "?";
    const { min, max } = metricRange(b.metric);
    const inRange = (v: number) => v >= min && v <= max;
    if (b.metric.ceiling && !inRange(b.metric.ceiling.value)) err(file, `ceiling ${b.metric.ceiling.value} is outside ${min}–${max}`);
    if (b.metric.floor && !inRange(b.metric.floor.value)) err(file, `floor ${b.metric.floor.value} is outside ${min}–${max}`);
    if (b.human_baseline && !inRange(b.human_baseline.value)) err(file, `human baseline is outside ${min}–${max}`);
    if (b.released > today) err(file, `released ${b.released} is in the future`);

    (catalog.scores[b.id] ?? []).forEach((row, i) => {
      const at = `scores/${b.id}.yaml #${i + 1}`;
      if (!row.metric && !inRange(row.score)) err(at, `score ${row.score} is outside ${min}–${max}`);
      if (row.ci && !(row.ci[0] <= row.score && row.score <= row.ci[1])) err(at, `ci ${row.ci} does not contain ${row.score}`);
      if (row.date > today) err(at, `date ${row.date} is in the future`);
      if (row.date < b.released.slice(0, row.date.length)) err(at, `date ${row.date} is before the benchmark's release ${b.released}`);
      const released = models.get(row.model)?.released;
      if (released && row.date < released.slice(0, row.date.length)) err(at, `date ${row.date} is before ${row.model} was released (${released})`);
    });
  }
  return problems;

  function err(file: string, message: string) {
    problems.push({ level: "error", file, message });
  }
}
