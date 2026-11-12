import { z } from "zod";
import { primitives } from "./primitives.ts";
import { metricSchema } from "./metric-schema.ts";

const { id, date, url } = primitives;

/** Front matter of data/benchmarks/<id>.md. The Markdown body below it is the article. */
export const benchmarkSchema = z
  .object({
    id,
    name: z.string().min(1),
    aliases: z.array(z.string()).default([]),
    summary: z.string().min(10).max(240),
    publishers: z.array(id).min(1),
    released: date,
    versions: z
      .array(z.object({ version: z.string(), released: date.optional(), note: z.string().optional() }).strict())
      .default([]),
    areas: z.array(id).min(1),
    tags: z.array(z.string()).default([]),
    measures: z.enum(["capability", "propensity"]),
    format: z.enum(["dataset", "agentic", "environment", "arena", "composite"]),
    live: z.boolean().default(false),
    modality: z.array(z.enum(["text", "image", "video", "audio", "action", "3d", "tabular"])).min(1),
    openness: z.enum(["public", "gated", "private"]),
    size: z
      .object({ items: z.number().positive().optional(), unit: z.string().optional(), note: z.string().optional() })
      .strict()
      .optional(),
    metric: metricSchema,
    human_baseline: z
      .object({ value: z.number(), note: z.string().optional(), source: url.optional() })
      .strict()
      .optional(),
    derived_from: z.array(id).default([]),
    supersedes: z.array(id).default([]),
    related: z.array(id).default([]),
    links: z
      .object({
        website: url.optional(),
        paper: url.optional(),
        code: url.optional(),
        dataset: url.optional(),
        leaderboard: url.optional(),
        blog: url.optional(),
      })
      .strict()
      .refine((l) => Object.keys(l).length > 0, "at least one source link is required"),
    status_override: z
      .object({ status: z.enum(["saturated", "compromised"]), reason: z.string().min(10), source: url })
      .strict()
      .optional(),
    source_keys: z
      .object({
        epoch: z.array(z.string()).optional(),
        radar: z.array(z.string()).optional(),
        pwc: z.array(z.string()).optional(),
      })
      .strict()
      .optional(),
    review: z
      .object({
        state: z.enum(["unverified", "verified"]),
        drafted_by: z.enum(["llm", "human"]),
        verified_by: z.string().optional(),
      })
      .strict(),
  })
  .strict();

export type Benchmark = z.infer<typeof benchmarkSchema> & { body: string };
