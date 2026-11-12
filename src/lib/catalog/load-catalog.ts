import type { ZodType } from "zod";
import { benchmarkSchema, type Benchmark } from "../schema/benchmark-schema.ts";
import { modelSchema } from "../schema/model-schema.ts";
import { orgSchema } from "../schema/org-schema.ts";
import { scoreFileSchema } from "../schema/score-schema.ts";
import { topicSchema, type Topic } from "../schema/topic-schema.ts";
import type { Catalog, Problem } from "./catalog-types.ts";
import { readEntries, type RawEntry } from "./read-entries.ts";

/**
 * Parses data/ into a Catalog. Files that fail their schema are reported as problems
 * and left out, so one bad file never hides the rest.
 */
export function loadCatalog(dataDir: string): { catalog: Catalog; problems: Problem[] } {
  const problems: Problem[] = [];
  const files = new Map<object, string>();

  function parseAll<T extends object>(entries: RawEntry[], schema: ZodType<T>): { entry: RawEntry; value: T }[] {
    const out: { entry: RawEntry; value: T }[] = [];
    for (const entry of entries) {
      if (entry.error) {
        problems.push({ level: "error", file: entry.file, message: entry.error });
        continue;
      }
      const result = schema.safeParse(entry.data);
      if (!result.success) {
        for (const issue of result.error.issues) {
          const at = issue.path.length ? `${issue.path.join(".")}: ` : "";
          problems.push({ level: "error", file: entry.file, message: `${at}${issue.message}` });
        }
        continue;
      }
      files.set(result.data, entry.file);
      out.push({ entry, value: result.data });
    }
    return out;
  }

  const benchmarks = parseAll(readEntries(dataDir, "benchmarks", ".md"), benchmarkSchema).map(({ entry, value }) => {
    const benchmark: Benchmark = { ...value, body: entry.body ?? "" };
    files.set(benchmark, entry.file);
    return benchmark;
  });
  const topics = parseAll(readEntries(dataDir, "topics", ".md"), topicSchema).map(({ entry, value }) => {
    const topic: Topic = { ...value, body: entry.body ?? "" };
    files.set(topic, entry.file);
    return topic;
  });
  const models = parseAll(readEntries(dataDir, "models", ".yaml"), modelSchema).map((p) => p.value);
  const orgs = parseAll(readEntries(dataDir, "orgs", ".yaml"), orgSchema).map((p) => p.value);

  const scores: Catalog["scores"] = {};
  for (const { entry, value } of parseAll(readEntries(dataDir, "scores", ".yaml"), scoreFileSchema)) {
    scores[entry.stem] = value;
  }

  return { catalog: { benchmarks, models, orgs, topics, scores, files }, problems };
}
