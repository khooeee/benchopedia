import { z } from "zod";
import { primitives } from "./primitives.ts";

/** data/orgs/<id>.yaml — a benchmark publisher or model developer. */
export const orgSchema = z
  .object({
    id: primitives.id,
    name: z.string().min(1),
    type: z.enum(["academic", "lab", "startup", "company", "eval-org", "nonprofit", "government", "community", "individual"]),
    url: primitives.url.optional(),
    aliases: z.array(z.string()).default([]),
  })
  .strict();

export type Org = z.infer<typeof orgSchema>;
