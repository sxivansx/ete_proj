/**
 * Indirect CO-Attainment (Course End Survey).
 *
 *   A = Σ (Nₛ · Wₛ) / (N · 3)
 *
 *   Nₛ — number of students who agree on scale S
 *   Wₛ — weight assigned to scale S (Strongly Agree = 3, Agree = 2, Disagree = 1)
 *   N  — total number of responses
 *
 * Result is returned as a percentage in [0, 100], or null when N = 0.
 */
export const SCALE_WEIGHTS = { sa: 3, a: 2, d: 1 } as const;
export type ScaleKey = keyof typeof SCALE_WEIGHTS;

export interface IndirectInput {
  sa: number;
  a: number;
  d: number;
}

export interface IndirectResult {
  N: number;
  perScalePct: Record<ScaleKey, number | null>;
  weightedSum: number;
  attainmentPct: number | null;
}

export function computeIndirectAttainment(input: IndirectInput): IndirectResult {
  const counts: Record<ScaleKey, number> = {
    sa: Math.max(0, input.sa | 0),
    a: Math.max(0, input.a | 0),
    d: Math.max(0, input.d | 0),
  };
  const N = counts.sa + counts.a + counts.d;
  const maxW = Math.max(...Object.values(SCALE_WEIGHTS));
  const weightedSum =
    counts.sa * SCALE_WEIGHTS.sa +
    counts.a * SCALE_WEIGHTS.a +
    counts.d * SCALE_WEIGHTS.d;
  const attainmentPct = N > 0 ? (weightedSum / (N * maxW)) * 100 : null;
  const perScalePct: Record<ScaleKey, number | null> = {
    sa: N > 0 ? (counts.sa / N) * 100 : null,
    a: N > 0 ? (counts.a / N) * 100 : null,
    d: N > 0 ? (counts.d / N) * 100 : null,
  };
  return { N, perScalePct, weightedSum, attainmentPct };
}
