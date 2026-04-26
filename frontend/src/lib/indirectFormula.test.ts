import { expect, test } from "bun:test";
import { computeIndirectAttainment } from "./indirectFormula";

const round = (v: number | null, digits = 2) =>
  v == null ? null : Number(v.toFixed(digits));

test("sample from spec: 41 / 28 / 2 → 85%", () => {
  const r = computeIndirectAttainment({ sa: 41, a: 28, d: 2 });
  expect(r.N).toBe(71);
  expect(r.weightedSum).toBe(181); // 41*3 + 28*2 + 2*1
  expect(round(r.attainmentPct)).toBe(84.98);
  expect(Math.round(r.attainmentPct!)).toBe(85);
  expect(round(r.perScalePct.sa)).toBe(57.75);
  expect(round(r.perScalePct.a)).toBe(39.44);
  expect(round(r.perScalePct.d)).toBe(2.82);
});

test("all zero responses → null", () => {
  const r = computeIndirectAttainment({ sa: 0, a: 0, d: 0 });
  expect(r.N).toBe(0);
  expect(r.attainmentPct).toBeNull();
  expect(r.perScalePct.sa).toBeNull();
});

test("all strongly-agree → 100%", () => {
  const r = computeIndirectAttainment({ sa: 10, a: 0, d: 0 });
  expect(r.attainmentPct).toBe(100);
  expect(round(r.perScalePct.sa)).toBe(100);
});

test("all disagree → 33.33%", () => {
  const r = computeIndirectAttainment({ sa: 0, a: 0, d: 10 });
  expect(round(r.attainmentPct)).toBe(33.33);
});

test("all agree (middle weight) → 66.67%", () => {
  const r = computeIndirectAttainment({ sa: 0, a: 10, d: 0 });
  expect(round(r.attainmentPct)).toBe(66.67);
});

test("equal split 20/20/20 → 66.67%", () => {
  const r = computeIndirectAttainment({ sa: 20, a: 20, d: 20 });
  // weighted = 60 + 40 + 20 = 120; denom = 60 * 3 = 180; 120/180 = 66.66...
  expect(round(r.attainmentPct)).toBe(66.67);
});

test("50 SA / 50 A / 0 D → 83.33%", () => {
  const r = computeIndirectAttainment({ sa: 50, a: 50, d: 0 });
  // weighted = 150 + 100 + 0 = 250; denom = 100 * 3 = 300; 250/300 = 83.33%
  expect(round(r.attainmentPct)).toBe(83.33);
});

test("0 SA / 50 A / 50 D → 50%", () => {
  const r = computeIndirectAttainment({ sa: 0, a: 50, d: 50 });
  // weighted = 0 + 100 + 50 = 150; denom = 100 * 3 = 300; 150/300 = 50%
  expect(round(r.attainmentPct)).toBe(50);
});

test("negatives are clamped to 0", () => {
  const r = computeIndirectAttainment({ sa: -5, a: 10, d: 0 });
  expect(r.N).toBe(10);
  expect(round(r.attainmentPct)).toBe(66.67);
});

test("non-integer inputs are floored", () => {
  // bitwise | 0 truncates toward zero
  const r = computeIndirectAttainment({ sa: 41.9, a: 28.2, d: 2.1 });
  expect(r.N).toBe(71);
  expect(Math.round(r.attainmentPct!)).toBe(85);
});

test("final = direct·0.9 + indirect·0.1 — matches faculty sheet", () => {
  // From the spec screenshot, with indirect = 85:
  //   CO1: 64.37898 → 0.9*64.37898 + 0.1*85 = 66.441082
  //   CO2: 63.45608 → 65.610472
  //   CO3: 63.49841 → 65.648569
  //   CO4: 66.70740 → 68.536660
  const indirect = 85;
  const cases: [number, number][] = [
    [64.37898, 66.441082],
    [63.45608, 65.610472],
    [63.49841, 65.648569],
    [66.7074, 68.53666],
  ];
  for (const [direct, expected] of cases) {
    const final = direct * 0.9 + indirect * 0.1;
    expect(Number(final.toFixed(5))).toBe(Number(expected.toFixed(5)));
  }
});
