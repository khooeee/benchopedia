import { z } from "zod";
import { primitives } from "./primitives.ts";

/** One reported result, as a row in data/scores/<benchmark-id>.yaml. */
export const scoreSchema = z
  .object({
    model: primitives.id,
    version: z.string().optional(),
    metric: z.string().optional(),
    score: z.number(),
    ci: z.tuple([z.number(), z.number()]).optional(),
    date: primitives.date,
    setting: z
      .object({
        effort: z.string().optional(),
        tools: z.string().optional(),
        scaffold: z.string().optional(),
        shots: z.number().optional(),
        note: z.string().optional(),
      })
      .strict()
      .optional(),
    reported_by: z.enum(["benchmark-author", "model-developer", "third-party"]),
    via: z.string().optional(),
    source: primitives.url,
  })
  .strict();

export const scoreFileSchema = z.array(scoreSchema);

export type Score = z.infer<typeof scoreSchema>;
