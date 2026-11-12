import assert from "node:assert/strict";
import { test } from "node:test";
import type { Catalog } from "../src/lib/catalog/catalog-types.ts";
import { runChecks } from "../src/lib/checks/run-checks.ts";
import { makeBenchmark, score } from "./fixtures/make-benchmark.ts";

const ARTICLE = ["What it is", "Example task", "Why it matters", "Caveats", "History"].map((h) => `## ${h}\n\nText.`).join("\n\n");

function catalog(overrides: Partial<Catalog> = {}): Catalog {
  const benchmark = { ...makeBenchmark(), body: ARTICLE };
  const base: Catalog = {
    benchmarks: [benchmark],
    models: [{ id: "m1", name: "Model One", aliases: [], released: "2024-01-01" }],
    orgs: [{ id: "acme", name: "Acme", type: "lab", aliases: [] }],
    topics: [{ id: "knowledge", name: "Knowledge", summary: "Knowledge topic.", order: 1, body: "" }],
    scores: { demo: [score("m1", 50, "2024-06-01")] },
    files: new Map(),
    ...overrides,
  };
  base.benchmarks.forEach((b) => base.files.set(b, `benchmarks/${b.id}.md`));
  base.models.forEach((m) => base.files.set(m, `models/${m.id}.yaml`));
  base.orgs.forEach((o) => base.files.set(o, `orgs/${o.id}.yaml`));
  base.topics.forEach((t) => base.files.set(t, `topics/${t.id}.md`));
  return base;
}

const errors = (c: Catalog) => runChecks(c, "2026-11-11").filter((p) => p.level === "error").map((p) => p.message);

test("a clean catalog has no errors", () => {
  assert.deepEqual(errors(catalog()), []);
});

test("unknown references are errors", () => {
  const c = catalog({ scores: { demo: [score("ghost", 50, "2024-06-01")] } });
  assert.ok(errors(c).some((m) => m.includes('unknown model "ghost"')));
});

test("scores outside the metric range are errors", () => {
  const c = catalog({ scores: { demo: [score("m1", 140, "2024-06-01")] } });
  assert.ok(errors(c).some((m) => m.includes("outside 0–100")));
});

test("a score dated before the model existed is an error", () => {
  const c = catalog({ scores: { demo: [score("m1", 50, "2023-06-01")] } });
  assert.ok(errors(c).some((m) => m.includes("before m1 was released")));
});

test("duplicate rows are errors", () => {
  const row = score("m1", 50, "2024-06-01");
  assert.ok(errors(catalog({ scores: { demo: [row, { ...row }] } })).some((m) => m.includes("duplicate")));
});

test("alias collisions between models are errors", () => {
  const models = [
    { id: "m1", name: "Model One", aliases: ["shared"], released: "2024-01-01" },
    { id: "m2", name: "Model Two", aliases: ["Shared"] },
  ];
  assert.ok(errors(catalog({ models })).some((m) => m.includes('"shared" is also used by "m1"')));
});

test("lineage loops are errors", () => {
  const a = { ...makeBenchmark({ id: "a", derived_from: ["b"] }), body: ARTICLE };
  const b = { ...makeBenchmark({ id: "b", derived_from: ["a"] }), body: ARTICLE };
  assert.ok(errors(catalog({ benchmarks: [a, b], scores: {} })).some((m) => m.includes("lineage loop")));
});

test("missing article sections are errors", () => {
  const b = { ...makeBenchmark(), body: "## What it is\n\nOnly this." };
  assert.ok(errors(catalog({ benchmarks: [b] })).some((m) => m.includes('missing section "## Caveats"')));
});
