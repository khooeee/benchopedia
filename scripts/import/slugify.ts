/** "Claude Opus 4.5 (Nov 2025)" → "claude-opus-4-5-nov-2025": a valid entity id. */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
