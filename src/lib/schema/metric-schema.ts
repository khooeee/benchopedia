import { z } from "zod";
import { primitives } from "./primitives.ts";

/**
 * The headline metric that drives saturation.
 * `range` bounds every valid score. `ceiling` is the best score realistically achievable
 * (label noise, ambiguity) and is omitted for open-ended metrics such as Elo or time horizons.
 * `floor` is the score of a trivial system (random guessing); it defaults to the worst end of `range`.
 */
export const metricSchema = z
  .object({
    name: z.string().min(1),
    unit: z.enum(["percent", "score", "elo", "minutes", "dollars", "ratio", "points"]),
    direction: z.enum(["higher", "lower"]),
    range: z.object({ min: z.number(), max: z.number() }).strict().optional(),
    ceiling: z
      .object({ value: z.number(), note: z.string().optional(), source: primitives.url.optional() })
      .strict()
      .optional(),
    floor: z.object({ value: z.number(), note: z.string().optional() }).strict().optional(),
  })
  .strict();

export type Metric = z.infer<typeof metricSchema>;
