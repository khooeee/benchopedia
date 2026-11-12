import { z } from "zod";
import { primitives } from "./primitives.ts";

/** Front matter of data/topics/<id>.md. The Markdown body is the topic introduction. */
export const topicSchema = z
  .object({
    id: primitives.id,
    name: z.string().min(1),
    summary: z.string().min(10).max(240),
    order: z.number().int().default(100),
  })
  .strict();

export type Topic = z.infer<typeof topicSchema> & { body: string };
