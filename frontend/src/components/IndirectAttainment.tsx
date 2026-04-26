import { useState } from "react";
import type { Block } from "../api";
import { computeIndirectAttainment } from "../lib/indirectFormula";

const SCALES = [
  { key: "sa", label: "STRONGLY AGREE", weight: 3 },
  { key: "a", label: "AGREE", weight: 2 },
  { key: "d", label: "DISAGREE", weight: 1 },
] as const;

type ScaleKey = (typeof SCALES)[number]["key"];

const DIRECT_W = 0.9;
const INDIRECT_W = 0.1;

interface Props {
  cos: number[];
  direct: Block;
}

function FormulaCard() {
  return (
    <div className="formula-card">
      <div className="formula-title">
        Process used for Indirect Assessment (Course End Survey)
      </div>
      <div className="formula-body">
        <span className="formula-lhs">A =</span>
        <span className="formula-frac">
          <span className="formula-num">
            <span className="formula-sigma">
              <span className="formula-sigma-top">3</span>
              <span className="formula-sigma-glyph">Σ</span>
              <span className="formula-sigma-bot">S = 1</span>
            </span>
            <span className="formula-term">
              N<sub>S</sub> · W<sub>S</sub>
            </span>
          </span>
          <span className="formula-bar" />
          <span className="formula-den">N · 3</span>
        </span>
      </div>
      <ul className="formula-legend">
        <li>
          <b>Nₛ</b> — number of students who agree on scale S
        </li>
        <li>
          <b>Wₛ</b> — weightage assigned to scale S
        </li>
        <li>
          <b>N</b> — total number of students (responses)
        </li>
      </ul>
    </div>
  );
}

function fmt(v: number | null | undefined, digits = 2): string {
  return v == null ? "—" : v.toFixed(digits);
}

function cellClass(v: number | null | undefined, target = 60): string {
  if (v == null) return "cell muted";
  return v >= target ? "cell good" : "cell bad";
}

export function IndirectAttainment({ cos, direct }: Props) {
  const [responses, setResponses] = useState<Record<ScaleKey, string>>({
    sa: "",
    a: "",
    d: "",
  });

  function setVal(k: ScaleKey, v: string) {
    if (v === "" || /^\d+$/.test(v)) {
      setResponses((r) => ({ ...r, [k]: v }));
    }
  }

  const { N, perScalePct, attainmentPct } = computeIndirectAttainment({
    sa: Number(responses.sa) || 0,
    a: Number(responses.a) || 0,
    d: Number(responses.d) || 0,
  });

  const finalPerCo: Record<number, number | null> = {};
  for (const co of cos) {
    const d = direct.per_co[String(co)];
    if (d == null || attainmentPct == null) {
      finalPerCo[co] = null;
    } else {
      finalPerCo[co] = d * DIRECT_W + attainmentPct * INDIRECT_W;
    }
  }

  return (
    <section className="panel">
      <h2>Indirect CO-Attainment</h2>

      <FormulaCard />

      <table className="matrix indirect">
        <thead>
          <tr>
            <th>Scale</th>
            <th>Responses</th>
            <th>%</th>
            <th>Weightage</th>
            <th>Final</th>
          </tr>
        </thead>
        <tbody>
          {SCALES.map((s, i) => {
            const pct = perScalePct[s.key];
            return (
              <tr key={s.key} className="row">
                <td className="label">{s.label}</td>
                <td>
                  <input
                    type="text"
                    inputMode="numeric"
                    className="indirect-input"
                    value={responses[s.key]}
                    onChange={(e) => setVal(s.key, e.target.value)}
                    placeholder="0"
                  />
                </td>
                <td>{pct == null ? "—" : pct.toFixed(0) + "%"}</td>
                <td>{s.weight}</td>
                {i === 0 && (
                  <td
                    rowSpan={SCALES.length + 1}
                    className={
                      attainmentPct == null
                        ? "cell muted final-cell"
                        : attainmentPct >= 60
                          ? "cell good final-cell"
                          : "cell bad final-cell"
                    }
                  >
                    {attainmentPct == null
                      ? "—"
                      : attainmentPct.toFixed(0) + "%"}
                  </td>
                )}
              </tr>
            );
          })}
          <tr className="row emphasis">
            <td className="label">TOTAL</td>
            <td>{N || "—"}</td>
            <td>{N > 0 ? "100%" : "—"}</td>
            <td>—</td>
          </tr>
        </tbody>
      </table>

      <div style={{ height: 20 }} />

      <table className="matrix">
        <thead>
          <tr>
            <th colSpan={cos.length + 1} style={{ textAlign: "center" }}>
              In-Direct CO-Attainment
            </th>
          </tr>
          <tr>
            <th>COs</th>
            {cos.map((co) => (
              <th key={co}>CO{co}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="row emphasis">
            <td className="label">CES</td>
            {cos.map((co) => (
              <td key={co} className={cellClass(attainmentPct)}>
                {fmt(attainmentPct, 0)}
              </td>
            ))}
          </tr>
        </tbody>
      </table>

      <div style={{ height: 20 }} />

      <table className="matrix">
        <thead>
          <tr>
            <th colSpan={cos.length + 1} style={{ textAlign: "center" }}>
              Final CO-Attainment
            </th>
          </tr>
          <tr>
            <th>COs</th>
            {cos.map((co) => (
              <th key={co}>CO{co}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="row">
            <td className="label">Direct</td>
            {cos.map((co) => {
              const v = direct.per_co[String(co)];
              return (
                <td key={co} className={cellClass(v)}>
                  {fmt(v, 5)}
                </td>
              );
            })}
          </tr>
          <tr className="row">
            <td className="label">In-Direct</td>
            {cos.map((co) => (
              <td key={co} className={cellClass(attainmentPct)}>
                {fmt(attainmentPct, 5)}
              </td>
            ))}
          </tr>
          <tr className="row emphasis">
            <td className="label">Direct·90% + In-Direct·10%</td>
            {cos.map((co) => (
              <td key={co} className={cellClass(finalPerCo[co])}>
                {fmt(finalPerCo[co], 5)}
              </td>
            ))}
          </tr>
        </tbody>
      </table>

      <p className="legend">
        <span className="cell good inline">≥ 60%</span>{" "}
        <span className="cell bad inline">&lt; 60%</span>{" "}
        <span className="cell muted inline">no data</span>
      </p>
      <p className="legend" style={{ marginTop: 6 }}>
        Note: CO1 Direct may differ by ~1% from the faculty sheet — known
        bug in the template (<code>CO-Attainment!C4</code> points at the
        cross-CO mean instead of the CO1 aggregate). Our calculator uses
        the correct per-CO value.
      </p>
    </section>
  );
}
