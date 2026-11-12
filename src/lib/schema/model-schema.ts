import { z } from "zod";
import { primitives } from "./primitives.ts";

/** data/models/<id>.yaml — one released model, snapshot, or published system. */
export const modelSchema = z
  .object({
    id: primitives.id,
    name: z.string().min(1),
    developer: primitives.id.optional(),
    family: z.string().optional(),
    released: primitives.date.optional(),
    open_weights: z.boolean().optional(),
    aliases: z.array(z.string()).default([]),
  })
  .strict();

export type Model = z.infer<typeof modelSchema>;
