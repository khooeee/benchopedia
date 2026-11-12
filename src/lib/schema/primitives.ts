import { z } from "zod";

/** Shared building blocks for every entity schema. */
export const primitives = {
  id: z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, "ids are lowercase kebab-case"),
  /** YYYY, YYYY-MM or YYYY-MM-DD. YAML may hand us a Date, so normalise it to a string first. */
  date: z.preprocess(
    (v) => (v instanceof Date ? v.toISOString().slice(0, 10) : v),
    z.string().regex(/^\d{4}(-\d{2}(-\d{2})?)?$/, "dates are YYYY, YYYY-MM or YYYY-MM-DD"),
  ),
  url: z.url({ protocol: /^https?$/ }),
};
