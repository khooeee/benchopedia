import type { Catalog, Problem } from "../catalog/catalog-types.ts";
import { checkAliases } from "./check-aliases.ts";
import { checkArticles } from "./check-articles.ts";
import { checkDuplicateScores } from "./check-duplicate-scores.ts";
import { checkFileNames } from "./check-file-names.ts";
import { checkLineage } from "./check-lineage.ts";
import { checkNearDuplicates } from "./check-near-duplicates.ts";
import { checkReferences } from "./check-references.ts";
import { checkValues } from "./check-values.ts";

/** Runs every integrity check. Errors block a merge; warnings are for a human to look at. */
export function runChecks(catalog: Catalog, today: string): Problem[] {
  return [
    ...checkFileNames(catalog),
    ...checkAliases(catalog),
    ...checkReferences(catalog),
    ...checkValues(catalog, today),
    ...checkDuplicateScores(catalog),
    ...checkLineage(catalog),
    ...checkArticles(catalog),
    ...checkNearDuplicates(catalog),
  ];
}
