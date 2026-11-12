// Attaches dated results from Epoch AI and Benchmark Radar to every benchmark with `source_keys`.
// Hand-written rows (no `via`, or a `via` we do not import) are kept; imported rows are replaced.
// Usage: npm run fetch-sources && npm run import-scores
import { existsSync, writeFileSync } from "node:fs";
import { stringify } from "yaml";
import { loadCatalog } from "../src/lib/catalog/load-catalog.ts";
import type { Score } from "../src/lib/schema/score-schema.ts";
import { metricRange } from "../src/lib/saturation/metric-range.ts";
import { loadEpoch } from "./import/epoch-source.ts";
import type { ImportRow } from "./import/import-row.ts";
import { createModelRegistry } from "./import/model-registry.ts";
import { loadRadar } from "./import/radar-source.ts";

const SOURCES = ".cache/sources";
const DATA = process.env.DATA_DIR ?? "data";
const IMPORTED_VIA = /^(epoch|radar\/)/;
const today = new Date().toISOString().slice(0, 10);
const pad = (d: string) => (d.length === 4 ? `${d}-01-01` : d.length === 7 ? `${d}-01` : d);

const { catalog } = loadCatalog(DATA);
const epoch = loadEpoch(`${SOURCES}/epoch`);
const radar = loadRadar(`${SOURCES}/radar_scores.jsonl`);
const registry = createModelRegistry(catalog.models, catalog.orgs);

for (const benchmark of catalog.benchmarks) {
  const keys = benchmark.source_keys;
  if (!keys) continue;
  const { min, max } = metricRange(benchmark.metric);
  const series = [...(keys.epoch ?? []).map(epoch), ...(keys.radar ?? []).map(radar)];

  const best = new Map<string, Score>();
  for (const rows of series) {
    const asFraction = benchmark.metric.unit === "percent" && rows.length > 0 && rows.every((r) => Math.abs(r.value) <= 1);
    for (const row of rows) {
      const score = toScore(row, asFraction ? row.value * 100 : row.value, pad(benchmark.released));
      if (!score || score.score < min || score.score > max) continue;
      const key = JSON.stringify([score.model, score.setting?.effort, score.source]);
      const prev = best.get(key);
      const better = benchmark.metric.direction === "higher" ? (a: number, b: number) => a > b : (a: number, b: number) => a < b;
      if (!prev || better(score.score, prev.score)) best.set(key, score);
    }
  }

  const kept = (catalog.scores[benchmark.id] ?? []).filter((r) => !IMPORTED_VIA.test(r.via ?? ""));
  const rows = [...kept, ...best.values()].sort((a, b) => a.date.localeCompare(b.date) || a.model.localeCompare(b.model));
  if (rows.length) writeFileSync(`${DATA}/scores/${benchmark.id}.yaml`, stringify(rows, { lineWidth: 0 }));
  console.log(`${benchmark.id}: ${best.size} imported, ${kept.length} hand-written`);
}

for (const model of registry.created) {
  const file = `${DATA}/models/${model.id}.yaml`;
  if (!existsSync(file)) writeFileSync(file, stringify(strip(model), { lineWidth: 0 }));
}
for (const org of registry.createdOrgs) {
  const file = `${DATA}/orgs/${org.id}.yaml`;
  if (!existsSync(file)) writeFileSync(file, stringify(strip(org), { lineWidth: 0 }));
}
console.log(`\n${registry.created.length} new models, ${registry.createdOrgs.length} new orgs`);

function toScore(row: ImportRow, value: number, benchmarkReleased: string): Score | undefined {
  const model = registry.resolve(row);
  const floors = [row.date, benchmarkReleased, model.released ? pad(model.released) : ""].filter(Boolean);
  const date = floors.reduce((a, b) => (a > b ? a : b));
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || date > today) return undefined;
  return {
    model: model.id,
    score: Math.round(value * 1000) / 1000,
    date,
    ...(row.effort ? { setting: { effort: row.effort } } : {}),
    reported_by: row.reportedBy,
    via: row.via,
    source: row.source,
  };
}

function strip<T extends object>(o: T): T {
  return Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && !(Array.isArray(v) && !v.length))) as T;
}
