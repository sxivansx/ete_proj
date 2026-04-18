import type { AttainmentResult, Block } from "../api";

function fmt(v: number | null | undefined): string {
  return v == null ? "—" : v.toFixed(2);
}

function cellClass(v: number | null | undefined, target = 60): string {
  if (v == null) return "cell muted";
  return v >= target ? "cell good" : "cell bad";
}

interface Props {
  result: AttainmentResult;
}

function MatrixTable({
  title,
  rows,
  cos,
  emphasisLabel,
}: {
  title: string;
  rows: { label: string; block: Block }[];
  cos: number[];
  emphasisLabel?: string;
}) {
  return (
    <table className="matrix">
      <thead>
        <tr>
          <th colSpan={cos.length + 1} style={{ textAlign: "center" }}>
            {title}
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
        {rows.map(({ label, block }) => (
          <tr
            key={label}
            className={
              label === emphasisLabel ? "row emphasis" : "row"
            }
          >
            <td className="label">{label}</td>
            {cos.map((co) => {
              const v = block.per_co[String(co)];
              return (
                <td key={co} className={cellClass(v)}>
                  {fmt(v)}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function AttainmentMatrix({ result }: Props) {
  const cos = result.course.co_numbers;

  const cieRows: { label: string; block: Block }[] = [
    { label: "IA(1+2+3)", block: result.ia_average },
    ...(result.aat ? [{ label: "ASSIGNMENT", block: result.aat }] : []),
    { label: "CIE CO-Attainment", block: result.cie },
  ];

  const directRows: { label: string; block: Block }[] = [
    { label: "CIE", block: result.cie },
    ...(result.see ? [{ label: "SEE", block: result.see }] : []),
    { label: "CIE*60% +SEE*40%", block: result.direct },
  ];

  return (
    <section className="panel">
      <MatrixTable
        title="CIE CO-Attainment"
        rows={cieRows}
        cos={cos}
        emphasisLabel="CIE CO-Attainment"
      />
      <div style={{ height: 20 }} />
      <MatrixTable
        title="Direct CO-Attainment"
        rows={directRows}
        cos={cos}
        emphasisLabel="CIE*60% +SEE*40%"
      />
      <p className="legend">
        <span className="cell good inline">≥ 60%</span>{" "}
        <span className="cell bad inline">&lt; 60%</span>{" "}
        <span className="cell muted inline">no data</span>
      </p>
    </section>
  );
}
