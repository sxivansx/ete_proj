import { useState } from "react";
import { uploadWorkbook, type AttainmentResult } from "./api";
import { Uploader } from "./components/Uploader";
import { SheetView } from "./components/SheetView";
import { AttainmentMatrix } from "./components/AttainmentMatrix";

export function App() {
  const [result, setResult] = useState<AttainmentResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setFilename(file.name);
    try {
      const r = await uploadWorkbook(file);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
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
          <pre>{error}</pre>
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
        </>
      )}
    </div>
  );
}
