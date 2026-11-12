import type { Benchmark } from "../schema/benchmark-schema.ts";
import type { Model } from "../schema/model-schema.ts";
import type { Org } from "../schema/org-schema.ts";
import type { Score } from "../schema/score-schema.ts";
import type { Topic } from "../schema/topic-schema.ts";

/** Every entity in data/, parsed and keyed by the file it came from. */
export type Catalog = {
  benchmarks: Benchmark[];
  models: Model[];
  orgs: Org[];
  topics: Topic[];
  /** Benchmark id → its score rows. */
  scores: Record<string, Score[]>;
  /** Entity → file path relative to data/, for error messages. */
  files: Map<object, string>;
};

export type Problem = { level: "error" | "warning"; file: string; message: string };
