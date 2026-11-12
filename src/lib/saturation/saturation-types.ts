import type { Score } from "../schema/score-schema.ts";

export type SaturationStatus = "headroom" | "approaching" | "saturated" | "compromised" | "unknown";

export type Saturation = {
  status: SaturationStatus;
  /** One line explaining the status, shown next to the badge. */
  reason: string;
  /** Best headline result on the latest scored version. */
  best?: Score;
  /** Share of the floor-to-ceiling gap closed by the best result, 0–1. Undefined for open-ended metrics. */
  progress?: number;
  /** Gap between the #1 and #5 models within a year of the best result, in metric units. */
  spread?: number;
  /** Improvement of the best result over the preceding 12 months, in metric units. */
  yearGain?: number;
  /** Rows the status was computed from (headline metric, latest scored version). */
  rows: Score[];
};
