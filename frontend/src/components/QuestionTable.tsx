import { useState } from "react";
import type { Question } from "../api";
import { CoBubbles } from "./CoBubble";

function fmt(v: number | null): string {
  return v == null ? "—" : v.toFixed(2);
}

interface Props {
  questions: Question[];
}

export function QuestionTable({ questions }: Props) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? questions : questions.slice(0, 12);

  return (
    <section className="panel">
      <h2>Per-question breakdown</h2>
      <table className="questions">
        <thead>
          <tr>
            <th>Col</th>
            <th>Label</th>
            <th>Kind</th>
            <th>IA</th>
            <th>CO</th>
            <th>Max</th>
            <th>Pass</th>
            <th>Attempted</th>
            <th>Attainment</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((q) => (
            <tr key={q.column_index}>
              <td>{q.column_index}</td>
              <td>{q.label}</td>
              <td>{q.kind}</td>
              <td>{q.ia_index ?? "—"}</td>
              <td>{q.co_tags.length ? <CoBubbles tags={q.co_tags} /> : "—"}</td>
              <td>{q.max_marks}</td>
              <td>{q.pass_count}</td>
              <td>{q.attempt_count}</td>
              <td className={q.attainment != null && q.attainment >= 60 ? "good" : "bad"}>
                {fmt(q.attainment)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {questions.length > 12 && (
        <button className="link" onClick={() => setShowAll((v) => !v)}>
          {showAll ? "Show first 12" : `Show all ${questions.length}`}
        </button>
      )}
    </section>
  );
}
