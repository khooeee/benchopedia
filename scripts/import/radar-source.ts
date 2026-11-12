import { readFileSync } from "node:fs";
import type { ImportRow } from "./import-row.ts";

type RadarScore = {
  key: string;
  source: string;
  model_name: string;
  organization?: string;
  value: unknown;
  reported_date?: string;
  reported_by: string;
  source_url?: string;
};

const EFFORT = /\b(minimal|low|medium|high|xhigh|max)\b/i;

/**
 * Reads Benchmark Radar's scores.jsonl and returns results by series key
 * (for example "artificial-analysis:gpqa-diamond").
 */
export function loadRadar(file: string): (key: string) => ImportRow[] {
  const byKey = new Map<string, RadarScore[]>();
  for (const line of readFileSync(file, "utf8").split("\n")) {
    if (!line.trim()) continue;
    const row = JSON.parse(line) as RadarScore;
    if (row.source === "benchmark_saturation") continue;
    byKey.set(row.key, [...(byKey.get(row.key) ?? []), row]);
  }

  return (key) =>
    (byKey.get(key) ?? []).flatMap((r): ImportRow[] => {
      if (typeof r.value !== "number" || !r.reported_date || !r.source_url) return [];
      const setting = /\(([^)]*)\)/.exec(r.model_name)?.[1];
      const name = r.model_name.replace(/\s*\([^)]*\)/g, "").trim();
      return [
        {
          modelName: name,
          modelAliases: [],
          developer: r.organization || undefined,
          value: r.value,
          date: r.reported_date.slice(0, 10),
          effort: setting ? (EFFORT.exec(setting)?.[1]?.toLowerCase() ?? setting) : undefined,
          reportedBy: r.reported_by === "self_reported" ? "model-developer" : "third-party",
          via: `radar/${r.source.replace(/_/g, "-")}`,
          source: r.source_url,
        },
      ];
    });
}
