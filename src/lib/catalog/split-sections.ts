/** Splits Markdown into "## Heading" → trimmed section text. Text before the first heading is dropped. */
export function splitSections(markdown: string): Map<string, string> {
  const sections = new Map<string, string>();
  let heading: string | null = null;
  let lines: string[] = [];
  const flush = () => {
    if (heading !== null) sections.set(heading, lines.join("\n").trim());
  };
  for (const line of markdown.split("\n")) {
    const match = /^##\s+(.+?)\s*$/.exec(line);
    if (match) {
      flush();
      heading = match[1];
      lines = [];
    } else {
      lines.push(line);
    }
  }
  flush();
  return sections;
}
