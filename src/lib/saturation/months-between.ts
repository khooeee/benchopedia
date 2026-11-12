/** Whole months from one YYYY[-MM[-DD]] date to another. Negative when `to` is earlier. */
export function monthsBetween(from: string, to: string): number {
  const [fy, fm = 1] = from.split("-").map(Number);
  const [ty, tm = 1] = to.split("-").map(Number);
  return (ty - fy) * 12 + (tm - fm);
}
