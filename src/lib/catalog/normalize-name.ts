/** Folds case, punctuation and spacing so "SWE-bench Verified" and "swe_bench verified" compare equal. */
export function normalizeName(name: string): string {
  return name
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9.]+/g, "");
}
