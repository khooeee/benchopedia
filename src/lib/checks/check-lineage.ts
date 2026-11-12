import type { Catalog, Problem } from "../catalog/catalog-types.ts";

/** derived_from and supersedes must form a family tree, never a loop. */
export function checkLineage(catalog: Catalog): Problem[] {
  const parents = new Map(catalog.benchmarks.map((b) => [b.id, [...b.derived_from, ...b.supersedes]]));
  const problems: Problem[] = [];
  for (const b of catalog.benchmarks) {
    const path = findPathBack(b.id, b.id, parents, new Set());
    if (path) {
      problems.push({ level: "error", file: catalog.files.get(b) ?? "?", message: `lineage loop: ${[b.id, ...path].join(" → ")}` });
    }
  }
  return problems;
}

function findPathBack(start: string, at: string, parents: Map<string, string[]>, seen: Set<string>): string[] | null {
  for (const parent of parents.get(at) ?? []) {
    if (parent === start) return [parent];
    if (seen.has(parent)) continue;
    seen.add(parent);
    const rest = findPathBack(start, parent, parents, seen);
    if (rest) return [parent, ...rest];
  }
  return null;
}
