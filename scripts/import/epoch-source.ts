import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { parse } from "csv-parse/sync";
import type { ImportRow } from "./import-row.ts";

type CsvRow = Record<string, string>;

/** Where Epoch's metadata points at a column that is not our headline metric. */
const COLUMN_OVERRIDES: Record<string, { column: string; scale: number }> = {
  "METR Time Horizons": { column: "Time horizon", scale: 1 },
};

const EFFORTS = new Set(["minimal", "low", "medium", "high", "xhigh", "max", "unknown", "none"]);

/** Reads Epoch AI's benchmark_data.zip (extracted) and returns results by Epoch benchmark name. */
export function loadEpoch(dir: string): (benchmarkName: string) => ImportRow[] {
  const read = (file: string): CsvRow[] => parse(readFileSync(join(dir, file)), { columns: true, skip_empty_lines: true });
  const meta = new Map(read("benchmark_metadata.csv").map((r) => [r.benchmark, r]));
  const models = new Map(read("model_metadata.csv").filter((r) => r.model_version).map((r) => [r.model_version, r]));

  return (name) => {
    const m = meta.get(name);
    if (!m?.source_file || !existsSync(join(dir, m.source_file))) return [];
    const internal = !m.source_file.endsWith("_external.csv");
    const { column, scale } = COLUMN_OVERRIDES[name] ?? { column: m.score_column, scale: Number(m.scale) || 1 };

    return read(m.source_file).flatMap((r): ImportRow[] => {
      const value = Number.parseFloat(r[column]);
      const version = r["Model version"];
      if (!version || !Number.isFinite(value)) return [];
      const [base, suffix] = splitEffort(version);
      const info = models.get(version) ?? models.get(base);
      const effort = r["Reasoning effort"] || (suffix && suffix !== "unknown" ? suffix : undefined);
      const sourceText = r["Source"] ?? "";
      const link = [r["Source link"], r["Source link (site from table)"], sourceText].find((s) => /^https?:\/\//.test(s ?? ""));
      return [
        {
          modelName: info?.model_group || base,
          modelAliases: [base],
          developer: info?.organization || r["Organization"] || undefined,
          released: info?.date || r["Release date"] || undefined,
          openWeights: info?.accessibility ? info.accessibility.startsWith("Open weights") : undefined,
          value: value * scale,
          date: (r["Started at"] || r["Release date"] || "").slice(0, 10),
          effort,
          reportedBy: internal || !/model card|system card|technical report|announcement|blog/i.test(sourceText) ? "third-party" : "model-developer",
          via: "epoch",
          source: link ?? "https://epoch.ai/benchmarks",
        },
      ];
    });
  };
}

function splitEffort(version: string): [string, string | undefined] {
  const i = version.lastIndexOf("_");
  if (i > 0 && EFFORTS.has(version.slice(i + 1))) return [version.slice(0, i), version.slice(i + 1)];
  return [version, undefined];
}
