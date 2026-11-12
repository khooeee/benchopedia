import { benchmarkSchema, type Benchmark } from "../../src/lib/schema/benchmark-schema.ts";
import type { Score } from "../../src/lib/schema/score-schema.ts";

/** A valid benchmark with sensible defaults; override any field. */
export function makeBenchmark(overrides: Record<string, unknown> = {}): Benchmark {
  const data = benchmarkSchema.parse({
    id: "demo",
    name: "Demo",
    summary: "A benchmark used in tests.",
    publishers: ["acme"],
    released: "2023-01-01",
    areas: ["knowledge"],
    measures: "capability",
    format: "dataset",
    modality: ["text"],
    openness: "public",
    metric: { name: "accuracy", unit: "percent", direction: "higher", ceiling: { value: 100 } },
    links: { paper: "https://example.com/paper" },
    review: { state: "unverified", drafted_by: "llm" },
    ...overrides,
  });
  return { ...data, body: "" };
}

/** A score row with defaults; `model` and `score` are the interesting parts. */
export function score(model: string, value: number, date: string, extra: Partial<Score> = {}): Score {
  return { model, score: value, date, reported_by: "third-party", source: "https://example.com/result", ...extra };
}
