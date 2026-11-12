import type { Catalog, Problem } from "../catalog/catalog-types.ts";

/** Every id that one file mentions must exist as its own file. */
export function checkReferences(catalog: Catalog): Problem[] {
  const problems: Problem[] = [];
  const benchmarkIds = new Set(catalog.benchmarks.map((b) => b.id));
  const modelIds = new Set(catalog.models.map((m) => m.id));
  const orgIds = new Set(catalog.orgs.map((o) => o.id));
  const topicIds = new Set(catalog.topics.map((t) => t.id));

  function expect(file: string, ids: string[], known: Set<string>, what: string) {
    for (const id of ids) {
      if (!known.has(id)) problems.push({ level: "error", file, message: `unknown ${what} "${id}"` });
    }
  }

  for (const b of catalog.benchmarks) {
    const file = catalog.files.get(b) ?? "?";
    expect(file, b.publishers, orgIds, "org (publishers)");
    expect(file, b.areas, topicIds, "topic (areas)");
    expect(file, [...b.derived_from, ...b.supersedes, ...b.related], benchmarkIds, "benchmark");
    if ([...b.derived_from, ...b.supersedes, ...b.related].includes(b.id)) {
      problems.push({ level: "error", file, message: "a benchmark cannot reference itself" });
    }
  }
  for (const m of catalog.models) {
    if (m.developer) expect(catalog.files.get(m) ?? "?", [m.developer], orgIds, "org (developer)");
  }
  for (const [benchmarkId, rows] of Object.entries(catalog.scores)) {
    const file = `scores/${benchmarkId}.yaml`;
    const benchmark = catalog.benchmarks.find((b) => b.id === benchmarkId);
    if (!benchmark) {
      problems.push({ level: "error", file, message: `no benchmark "${benchmarkId}" for this score file` });
      continue;
    }
    const versions = new Set(benchmark.versions.map((v) => v.version));
    rows.forEach((row, i) => {
      expect(`${file} #${i + 1}`, [row.model], modelIds, "model");
      if (row.version && !versions.has(row.version)) {
        problems.push({ level: "error", file: `${file} #${i + 1}`, message: `unknown version "${row.version}"` });
      }
    });
  }
  return problems;
}
