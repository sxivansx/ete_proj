import { useState } from "react";
import {
  TemplateValidationError,
  uploadWorkbook,
  type AttainmentResult,
  type TemplateViolation,
} from "./api";
import { Uploader } from "./components/Uploader";
import { SheetView } from "./components/SheetView";
import { AttainmentMatrix } from "./components/AttainmentMatrix";
import { IndirectAttainment } from "./components/IndirectAttainment";

export function App() {
  const [result, setResult] = useState<AttainmentResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [violations, setViolations] = useState<TemplateViolation[] | null>(
    null,
  );
  const [filename, setFilename] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setViolations(null);
    setFilename(file.name);
    try {
      const r = await uploadWorkbook(file);
      setResult(r);
    } catch (e) {
      if (e instanceof TemplateValidationError) {
        setError(e.message);
        setViolations(e.violations);
      } else {
        setError(e instanceof Error ? e.message : String(e));
        setViolations(null);
      }
      setResult(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>CO Attainment Dashboard</h1>
        <p className="subtitle">
          Upload a faculty CIE+SEE workbook to compute per-CO attainment.
        </p>
      </header>

      <Uploader onFile={handleFile} busy={busy} />

      {filename && !busy && !error && (
        <p className="filename">
          Loaded <code>{filename}</code>
        </p>
      )}

      {error && (
        <div className="error">
          <strong>Upload failed.</strong>
          {violations && violations.length > 0 ? (
            <>
              <p className="error-message">{error}</p>
              <table className="violation-table">
                <thead>
                  <tr>
                    <th>Cell</th>
                    <th>Issue</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {violations.map((v, i) => (
                    <tr key={i}>
                      <td className="violation-cell">{v.cell ?? "—"}</td>
                      <td className="violation-code">
                        <code>{v.code}</code>
                      </td>
                      <td>{v.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="hint">
                Fix the cells above and re-upload, or{" "}
                <a className="link" href="/api/v1/template" download>
                  download the blank template
                </a>{" "}
                and start fresh.
              </p>
            </>
          ) : (
            <pre>{error}</pre>
          )}
        </div>
      )}

      {result && !busy && (
        <>
          <section className="summary">
            <div>
              <span className="label">Course</span>
              <span className="value">{result.course.name || "—"}</span>
            </div>
            <div>
              <span className="label">Students</span>
              <span className="value">{result.course.students}</span>
            </div>
            <div>
              <span className="label">COs</span>
              <span className="value">
                {result.course.co_numbers.map((c) => `CO${c}`).join(", ")}
              </span>
            </div>
            <div>
              <span className="label">IAs</span>
              <span className="value">
                {result.course.ia_indices.map((i) => `IA${i}`).join(", ")}
              </span>
            </div>
          </section>

          <SheetView result={result} />
          <AttainmentMatrix result={result} />
          <IndirectAttainment
            cos={result.course.co_numbers}
            direct={result.direct}
          />
        </>
      )}
    </div>
  );
}
