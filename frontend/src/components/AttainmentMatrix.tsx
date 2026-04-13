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

export function AttainmentMatrix({ result }: Props) {
  const cos = result.course.co_numbers;
  const rows: Block[] = [
    ...result.ia_blocks,
    result.ia_average,
    ...(result.aat ? [result.aat] : []),
    result.cie,
    ...(result.see ? [result.see] : []),
    result.direct,
  ];

  return (
    <section className="panel">
      <h2>CO Attainment</h2>
      <table className="matrix">
        <thead>
          <tr>
            <th>Block</th>
            {cos.map((co) => (
              <th key={co}>CO{co}</th>
            ))}
            <th>Mean</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((b) => (
            <tr
              key={b.label}
              className={
                b.label === "Direct"
                  ? "row emphasis"
                  : b.label === "IA average" || b.label === "CIE"
                    ? "row subtle"
                    : "row"
              }
            >
              <td className="label">{b.label}</td>
              {cos.map((co) => {
                const v = b.per_co[String(co)];
                return (
                  <td key={co} className={cellClass(v)}>
                    {fmt(v)}
                  </td>
                );
              })}
              <td className={cellClass(b.mean)}>{fmt(b.mean)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="legend">
        <span className="cell good inline">≥ 60%</span>{" "}
        <span className="cell bad inline">&lt; 60%</span>{" "}
        <span className="cell muted inline">no data</span>
      </p>
    </section>
  );
}
