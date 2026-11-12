/**
 * Saturation thresholds, as shares of the floor-to-ceiling gap. The About page explains them.
 * - saturated: best result closes ≥95% of the gap, or ≥90% with the top five models within 2%.
 * - approaching: ≥80% closed, or the last year's pace would reach 95% within 12 months.
 * - unknown: not saturated and no new results for 18 months.
 */
export const SATURATION_RULES = {
  saturatedAt: 0.95,
  saturatedIfTightAt: 0.9,
  tightSpread: 0.02,
  approachingAt: 0.8,
  approachingWithinMonths: 12,
  staleAfterMonths: 18,
};
