import { normalizeName } from "../../src/lib/catalog/normalize-name.ts";
import type { Model } from "../../src/lib/schema/model-schema.ts";
import type { Org } from "../../src/lib/schema/org-schema.ts";
import type { ImportRow } from "./import-row.ts";
import { slugify } from "./slugify.ts";

const LABS = new Set(["openai", "anthropic", "google-deepmind", "meta", "xai", "mistral-ai", "deepseek", "moonshot", "alibaba", "zhipu-ai", "minimax", "cohere", "amazon", "microsoft", "nvidia"]);
const ORG_ALIASES: Record<string, string> = { "meta ai": "meta", "google": "google-deepmind", "deepmind": "google-deepmind", "mistral": "mistral-ai", "moonshot ai": "moonshot" };

/**
 * Matches imported model names to existing models by name or alias, creating
 * new model and org records for names it has never seen.
 */
export function createModelRegistry(models: Model[], orgs: Org[]) {
  const byName = new Map<string, Model>();
  const byId = new Map<string, Model>();
  const orgByName = new Map<string, Org>();
  const created: Model[] = [];
  const createdOrgs: Org[] = [];
  for (const m of models) index(m);
  for (const o of orgs) indexOrg(o);

  function index(m: Model) {
    byId.set(m.id, m);
    for (const n of [m.id, m.name, ...m.aliases]) if (!byName.has(normalizeName(n))) byName.set(normalizeName(n), m);
  }
  function indexOrg(o: Org) {
    for (const n of [o.id, o.name, ...o.aliases]) orgByName.set(normalizeName(n), o);
  }

  function resolveOrg(name: string | undefined): string | undefined {
    if (!name) return undefined;
    const known = orgByName.get(normalizeName(ORG_ALIASES[name.toLowerCase()] ?? name));
    if (known) return known.id;
    const id = slugify(name);
    if (!id) return undefined;
    const org: Org = { id, name, type: LABS.has(id) ? "lab" : "company", aliases: [] };
    createdOrgs.push(org);
    indexOrg(org);
    return id;
  }

  function resolve(row: ImportRow): Model {
    for (const n of [row.modelName, ...row.modelAliases]) {
      const hit = byName.get(normalizeName(n));
      if (hit) return hit;
    }
    const id = slugify(row.modelName);
    const existing = byId.get(id);
    if (existing) return existing;
    const aliases = row.modelAliases.filter((a) => normalizeName(a) !== normalizeName(row.modelName) && !byName.has(normalizeName(a)));
    const model: Model = {
      id,
      name: row.modelName,
      developer: resolveOrg(row.developer),
      released: row.released,
      open_weights: row.openWeights,
      aliases,
    };
    created.push(model);
    index(model);
    return model;
  }

  return { resolve, created, createdOrgs };
}
