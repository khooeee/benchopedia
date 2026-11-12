import type { Metric } from "../schema/metric-schema.ts";
import { metricRange } from "./metric-range.ts";

/** The trivial-system score: the explicit floor, else the worst end of the valid range. */
export function metricFloor(metric: Metric): number {
  const range = metricRange(metric);
  return metric.floor?.value ?? (metric.direction === "higher" ? range.min : range.max);
}

/**
 * Where a score sits between the trivial floor (0) and the realistic ceiling (1).
 * Works for both directions. Returns undefined for open-ended metrics with no ceiling.
 */
export function progress(value: number, metric: Metric): number | undefined {
  if (!metric.ceiling) return undefined;
  const floor = metricFloor(metric);
  const ceiling = metric.ceiling.value;
  if (!Number.isFinite(floor) || floor === ceiling) return undefined;
  return Math.max(0, Math.min(1, (value - floor) / (ceiling - floor)));
}
