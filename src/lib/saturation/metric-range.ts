import type { Metric } from "../schema/metric-schema.ts";

/** Valid score bounds. Percentages default to 0–100; other units are open unless the benchmark says so. */
export function metricRange(metric: Metric): { min: number; max: number } {
  if (metric.range) return metric.range;
  if (metric.unit === "percent") return { min: 0, max: 100 };
  return { min: -Infinity, max: Infinity };
}
