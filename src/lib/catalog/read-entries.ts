import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { parse } from "yaml";

export type RawEntry = { file: string; stem: string; data: unknown; body?: string; error?: string };

const FRONT_MATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/;

/** Reads every .yaml or .md file in one data/ subdirectory without validating it. */
export function readEntries(dataDir: string, subdir: string, ext: ".yaml" | ".md"): RawEntry[] {
  const dir = join(dataDir, subdir);
  const names = readdirSync(dir).filter((n) => n.endsWith(ext)).sort();
  return names.map((name) => {
    const file = `${subdir}/${name}`;
    const stem = name.slice(0, -ext.length);
    const text = readFileSync(join(dir, name), "utf8");
    try {
      if (ext === ".yaml") return { file, stem, data: parse(text) };
      const match = FRONT_MATTER.exec(text);
      if (!match) return { file, stem, data: null, error: "missing --- front matter ---" };
      return { file, stem, data: parse(match[1]), body: match[2].trim() };
    } catch (e) {
      return { file, stem, data: null, error: `invalid YAML: ${(e as Error).message.split("\n")[0]}` };
    }
  });
}
