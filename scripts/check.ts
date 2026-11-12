// Validates everything in data/. Exits non-zero on any error. Usage: npm run check [-- --quiet]
import { loadCatalog } from "../src/lib/catalog/load-catalog.ts";
import { runChecks } from "../src/lib/checks/run-checks.ts";

const quiet = process.argv.includes("--quiet");
const today = new Date().toISOString().slice(0, 10);
const { catalog, problems: parseProblems } = loadCatalog("data");
const problems = [...parseProblems, ...runChecks(catalog, today)];

const errors = problems.filter((p) => p.level === "error");
const warnings = problems.filter((p) => p.level === "warning");
for (const p of quiet ? errors : problems) console.log(`${p.level === "error" ? "✗" : "!"} ${p.file}: ${p.message}`);

const scoreRows = Object.values(catalog.scores).reduce((n, rows) => n + rows.length, 0);
console.log(
  `\n${catalog.benchmarks.length} benchmarks, ${catalog.models.length} models, ${catalog.orgs.length} orgs, ` +
    `${catalog.topics.length} topics, ${scoreRows} scores — ${errors.length} errors, ${warnings.length} warnings`,
);
process.exit(errors.length ? 1 : 0);
