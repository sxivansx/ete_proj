import { useRef, useState, type DragEvent } from "react";

interface Props {
  onFile: (f: File) => void;
  busy: boolean;
}

export function Uploader({ onFile, busy }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function acceptFile(f: File | null | undefined) {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".xlsx")) {
      alert("Please upload a .xlsx file");
      return;
    }
    onFile(f);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    acceptFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div className="upload-area">
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          hidden
          onChange={(e) => acceptFile(e.target.files?.[0])}
        />
        {busy ? (
          <p>Calculating…</p>
        ) : (
          <>
            <p className="main">Drop a .xlsx here</p>
            <p className="hint">or click to choose a file</p>
          </>
        )}
      </div>
      <p className="template-hint">
        First time?{" "}
        <a href="/api/v1/template" download>
          Download the blank template
        </a>{" "}
        to make sure your workbook matches the expected layout.
      </p>
    </div>
  );
}
