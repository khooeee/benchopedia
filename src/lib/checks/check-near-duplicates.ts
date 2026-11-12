import type { Catalog, Problem } from "../catalog/catalog-types.ts";
import { normalizeName } from "../catalog/normalize-name.ts";

type Named = { id: string; name: string };

/** Warns when two benchmarks or two models have names one or two edits apart. */
export function checkNearDuplicates(catalog: Catalog): Problem[] {
  return [...near(catalog, catalog.benchmarks), ...near(catalog, catalog.models)];
}

function near(catalog: Catalog, entities: Named[]): Problem[] {
  const problems: Problem[] = [];
  const keys = entities.map((e) => normalizeName(e.name));
  for (let i = 0; i < entities.length; i++) {
    for (let j = i + 1; j < entities.length; j++) {
      const a = keys[i];
      const b = keys[j];
      if (a.length < 6 || Math.abs(a.length - b.length) > 2) continue;
      // Version bumps like "terminalbench2" vs "terminalbench2.1" are expected, not duplicates.
      if (/\d/.test(a) || /\d/.test(b)) continue;
      if (editDistance(a, b) <= 2) {
        problems.push({
          level: "warning",
          file: catalog.files.get(entities[j]) ?? "?",
          message: `name looks like a near-duplicate of "${entities[i].id}"`,
        });
      }
    }
  }
  return problems;
}

function editDistance(a: string, b: string): number {
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    prev = cur;
  }
  return prev[b.length];
}
