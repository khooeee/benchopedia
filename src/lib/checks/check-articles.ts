import type { Catalog, Problem } from "../catalog/catalog-types.ts";
import { ARTICLE_SECTIONS } from "../catalog/article-sections.ts";
import { splitSections } from "../catalog/split-sections.ts";

/** Every article has the standard sections; verified articles have no empty ones. */
export function checkArticles(catalog: Catalog): Problem[] {
  const problems: Problem[] = [];
  for (const b of catalog.benchmarks) {
    const file = catalog.files.get(b) ?? "?";
    const sections = splitSections(b.body);
    for (const heading of ARTICLE_SECTIONS) {
      const text = sections.get(heading);
      if (text === undefined) {
        problems.push({ level: "error", file, message: `missing section "## ${heading}"` });
      } else if (!text && b.review.state === "verified") {
        problems.push({ level: "error", file, message: `verified article has empty section "## ${heading}"` });
      }
    }
  }
  return problems;
}
