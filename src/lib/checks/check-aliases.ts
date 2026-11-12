import type { Catalog, Problem } from "../catalog/catalog-types.ts";
import { normalizeName } from "../catalog/normalize-name.ts";

type Named = { id: string; name: string; aliases: string[] };

/** A name or alias must point to exactly one entity within its collection. */
export function checkAliases(catalog: Catalog): Problem[] {
  return [
    ...collisions(catalog, catalog.benchmarks),
    ...collisions(catalog, catalog.models),
    ...collisions(catalog, catalog.orgs),
  ];
}

function collisions(catalog: Catalog, entities: Named[]): Problem[] {
  const owner = new Map<string, string>();
  const problems: Problem[] = [];
  for (const entity of entities) {
    const keys = new Set([entity.id, entity.name, ...entity.aliases].map(normalizeName));
    for (const key of keys) {
      const other = owner.get(key);
      if (other && other !== entity.id) {
        problems.push({
          level: "error",
          file: catalog.files.get(entity) ?? "?",
          message: `name or alias "${key}" is also used by "${other}"`,
        });
      } else {
        owner.set(key, entity.id);
      }
    }
  }
  return problems;
}
