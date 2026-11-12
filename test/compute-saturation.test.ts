import assert from "node:assert/strict";
import { test } from "node:test";
import { computeSaturation } from "../src/lib/saturation/compute-saturation.ts";
import { makeBenchmark, score } from "./fixtures/make-benchmark.ts";

const TODAY = "2026-11-11";

test("no scores is unknown", () => {
  assert.equal(computeSaturation(makeBenchmark(), [], TODAY).status, "unknown");
});

test("best result near the ceiling is saturated", () => {
  const b = makeBenchmark({ metric: { name: "acc", unit: "percent", direction: "higher", floor: { value: 25 }, ceiling: { value: 93.5 } } });
  const s = computeSaturation(b, [score("a", 60, "2024-01"), score("b", 91, "2026-06")], TODAY);
  assert.equal(s.status, "saturated");
  assert.match(s.reason, /Best 91%/);
  assert.match(s.reason, /ceiling 93.5%/);
});

test("top five bunched together counts as saturated from 90%", () => {
  const b = makeBenchmark();
  const rows = ["a", "b", "c", "d", "e"].map((m, i) => score(m, 91 - i * 0.3, "2026-05"));
  assert.equal(computeSaturation(b, rows, TODAY).status, "saturated");
});

test("far from ceiling and slow is headroom", () => {
  const rows = [score("a", 10, "2025-06"), score("b", 14, "2026-08")];
  assert.equal(computeSaturation(makeBenchmark(), rows, TODAY).status, "headroom");
});

test("fast progress counts as approaching", () => {
  const rows = [score("a", 20, "2025-06"), score("b", 70, "2026-07")];
  assert.equal(computeSaturation(makeBenchmark(), rows, TODAY).status, "approaching");
});

test("lower-is-better metrics use the same scale", () => {
  const b = makeBenchmark({ metric: { name: "WER", unit: "percent", direction: "lower", ceiling: { value: 1 } } });
  const rows = [score("a", 30, "2016-01"), score("b", 1.4, "2026-01")];
  assert.equal(computeSaturation(b, rows, TODAY).status, "saturated");
});

test("open-ended metrics never saturate", () => {
  const b = makeBenchmark({ metric: { name: "time horizon", unit: "minutes", direction: "higher" } });
  const s = computeSaturation(b, [score("a", 400, "2026-09")], TODAY);
  assert.equal(s.status, "headroom");
  assert.match(s.reason, /open-ended/);
});

test("stale unsaturated results are unknown", () => {
  const s = computeSaturation(makeBenchmark(), [score("a", 40, "2022-01")], TODAY);
  assert.equal(s.status, "unknown");
  assert.match(s.reason, /No scores since 2022-01/);
});

test("override wins and keeps its reason", () => {
  const b = makeBenchmark({
    status_override: { status: "compromised", reason: "Test answers leaked online.", source: "https://example.com/leak" },
  });
  const s = computeSaturation(b, [score("a", 10, "2026-01")], TODAY);
  assert.equal(s.status, "compromised");
  assert.equal(s.reason, "Test answers leaked online.");
});

test("only the newest scored version counts", () => {
  const b = makeBenchmark({ versions: [{ version: "v1" }, { version: "v2" }] });
  const rows = [score("a", 99, "2025-01", { version: "v1" }), score("b", 30, "2026-06", { version: "v2" })];
  const s = computeSaturation(b, rows, TODAY);
  assert.equal(s.best?.score, 30);
  assert.equal(s.status, "headroom");
});
