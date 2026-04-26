// Thin fetch wrapper around the FastAPI backend.
//
// Via Vite's dev proxy (see vite.config.ts), /api/* hits http://localhost:8000.

/** One structural problem reported by the template validator. */
export interface TemplateViolation {
  code: string;
  message: string;
  row?: number;
  col?: number;
  cell?: string;
}

/** Thrown when the backend returns 422 with a list of template violations. */
export class TemplateValidationError extends Error {
  violations: TemplateViolation[];
  constructor(message: string, violations: TemplateViolation[]) {
    super(message);
    this.name = "TemplateValidationError";
    this.violations = violations;
  }
}

export interface Block {
  label: string;
  per_co: Record<string, number | null>;
  mean: number | null;
}

export interface ColumnHeader {
  column_index: number;
  label: string;
  kind: "question" | "tot" | "test" | "aat" | "final" | "see";
  ia_index: number | null;
  max_marks: number;
  co_tags: number[];
}

export interface RawStudent {
  sl_no: number;
  usn: string;
  marks: (number | string | null)[];
}

export interface Question {
  column_index: number;
  label: string;
  kind: "question" | "tot" | "test" | "aat" | "final" | "see";
  ia_index: number | null;
  max_marks: number;
  co_tags: number[];
  pass_count: number;
  attempt_count: number;
  attainment: number | null;
}

export interface AttainmentResult {
  course: {
    name: string;
    students: number;
    co_numbers: number[];
    ia_indices: number[];
  };
  columns: ColumnHeader[];
  raw_students: RawStudent[];
  per_question: Question[];
  ia_blocks: Block[];
  ia_average: Block;
  aat: Block | null;
  cie: Block;
  see: Block | null;
  direct: Block;
}

export async function uploadWorkbook(
  file: File,
  opts?: { passFraction?: number; cieWeight?: number },
): Promise<AttainmentResult> {
  const form = new FormData();
  form.append("file", file);

  const url = new URL("/api/v1/upload", window.location.origin);
  if (opts?.passFraction !== undefined) {
    url.searchParams.set("pass_fraction", String(opts.passFraction));
  }
  if (opts?.cieWeight !== undefined) {
    url.searchParams.set("cie_weight", String(opts.cieWeight));
  }

  const resp = await fetch(url.toString(), { method: "POST", body: form });
  if (!resp.ok) {
    const text = await resp.text();
    let parsed: unknown = null;
    try {
      parsed = JSON.parse(text);
    } catch {
      throw new Error(`${resp.status}: ${text}`);
    }
    // Structured 422 from the template validator:
    //   { detail: { error: "template_violations", message, violations: [...] } }
    const detail = (parsed as { detail?: unknown })?.detail;
    if (
      detail &&
      typeof detail === "object" &&
      (detail as { error?: string }).error === "template_violations"
    ) {
      const d = detail as {
        message: string;
        violations: TemplateViolation[];
      };
      throw new TemplateValidationError(d.message, d.violations);
    }
    const flat = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new Error(`${resp.status}: ${flat}`);
  }
  return resp.json();
}
