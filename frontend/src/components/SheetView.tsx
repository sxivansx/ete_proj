import { useState } from "react";
import type { AttainmentResult, Question } from "../api";
import { CoBubbles } from "./CoBubble";

function fmtMark(v: number | string | null): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  return Number.isInteger(v) ? String(v) : v.toFixed(1);
}

function fmtAtt(v: number | null): string {
  if (v == null) return "";
  return v.toFixed(4);
}

/** Build a lookup from column_index -> Question stats. */
function statsMap(questions: Question[]): Map<number, Question> {
  const m = new Map<number, Question>();
  for (const q of questions) m.set(q.column_index, q);
  return m;
}


interface Props {
  result: AttainmentResult;
}

export function SheetView({ result }: Props) {
  const { columns, raw_students, per_question } = result;
  const stats = statsMap(per_question);
  const [expanded, setExpanded] = useState(false);

  const COLLAPSED_ROWS = 15;
  const students = expanded
    ? raw_students
    : raw_students.slice(0, COLLAPSED_ROWS);

  return (
    <section className="panel sheet-panel">
      <h2>Sheet View</h2>
      <div className="sheet-scroll">
        <table className="sheet-table">
          <thead>
            {/* Row 1: Question labels */}
            <tr>
              <th className="sticky-col">Sl.No</th>
              <th className="sticky-col col-usn">USN</th>
              {columns.map((col) => (
                <th key={col.column_index} className="col-mark">
                  {col.label}
                </th>
              ))}
            </tr>
            {/* Row 2: CO tags */}
            <tr className="co-row">
              <th className="sticky-col"></th>
              <th className="sticky-col col-usn">CO</th>
              {columns.map((col) => (
                <th key={col.column_index} className="col-mark co-tag">
                  <CoBubbles tags={col.co_tags} />
                </th>
              ))}
            </tr>
            {/* Row 3: Max marks */}
            <tr className="max-row">
              <th className="sticky-col"></th>
              <th className="sticky-col col-usn">Max</th>
              {columns.map((col) => (
                <th key={col.column_index} className="col-mark">
                  {col.max_marks > 0 ? col.max_marks : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Student rows */}
            {students.map((s) => (
              <tr key={s.sl_no}>
                <td className="sticky-col">{s.sl_no}</td>
                <td className="sticky-col col-usn">{s.usn}</td>
                {s.marks.map((m, i) => (
                  <td key={i} className="col-mark">
                    {fmtMark(m)}
                  </td>
                ))}
              </tr>
            ))}

            {/* Expand/collapse row */}
            {raw_students.length > COLLAPSED_ROWS && (
              <tr>
                <td
                  colSpan={columns.length + 2}
                  className="expand-row"
                >
                  <button
                    className="link"
                    onClick={() => setExpanded((v) => !v)}
                  >
                    {expanded
                      ? `Show first ${COLLAPSED_ROWS}`
                      : `Show all ${raw_students.length} students`}
                  </button>
                </td>
              </tr>
            )}

            {/* Summary: count > 60% */}
            <tr className="summary-row highlight-row">
              <td className="sticky-col"></td>
              <td className="sticky-col col-usn summary-label">
                count &gt;60%
              </td>
              {columns.map((col) => {
                const q = stats.get(col.column_index);
                return (
                  <td key={col.column_index} className="col-mark">
                    {q ? q.pass_count : ""}
                  </td>
                );
              })}
            </tr>

            {/* Summary: count of attended */}
            <tr className="summary-row highlight-row">
              <td className="sticky-col"></td>
              <td className="sticky-col col-usn summary-label">
                count of attended
              </td>
              {columns.map((col) => {
                const q = stats.get(col.column_index);
                return (
                  <td key={col.column_index} className="col-mark">
                    {q ? q.attempt_count : ""}
                  </td>
                );
              })}
            </tr>

            {/* Summary: CO Attainment = B/A */}
            <tr className="summary-row highlight-row att-row">
              <td className="sticky-col"></td>
              <td className="sticky-col col-usn summary-label">
                CO Attainment = B/A
              </td>
              {columns.map((col) => {
                const q = stats.get(col.column_index);
                return (
                  <td
                    key={col.column_index}
                    className={`col-mark ${
                      q?.attainment != null
                        ? q.attainment >= 60
                          ? "good"
                          : "bad"
                        : ""
                    }`}
                  >
                    {q ? fmtAtt(q.attainment) : ""}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
