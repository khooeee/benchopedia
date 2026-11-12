import type { Catalog, Problem } from "../catalog/catalog-types.ts";

/** Each entity's id must match its file name, so ids are unique by construction. */
export function checkFileNames(catalog: Catalog): Problem[] {
  const problems: Problem[] = [];
  const entities = [...catalog.benchmarks, ...catalog.models, ...catalog.orgs, ...catalog.topics];
  for (const entity of entities) {
    const file = catalog.files.get(entity) ?? "?";
    const stem = file.replace(/^.*\//, "").replace(/\.(md|yaml)$/, "");
    if (stem !== entity.id) {
      problems.push({ level: "error", file, message: `id "${entity.id}" does not match file name "${stem}"` });
    }
  }
  return problems;
}
