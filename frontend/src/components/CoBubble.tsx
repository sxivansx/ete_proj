const CO_COLORS: Record<number, { bg: string; text: string }> = {
  1: { bg: "rgba(110, 168, 254, 0.18)", text: "#6ea8fe" },
  2: { bg: "rgba(62, 207, 142, 0.18)", text: "#3ecf8e" },
  3: { bg: "rgba(255, 179, 71, 0.18)", text: "#ffb347" },
  4: { bg: "rgba(204, 133, 255, 0.18)", text: "#cc85ff" },
  5: { bg: "rgba(255, 107, 107, 0.18)", text: "#ff6b6b" },
  6: { bg: "rgba(72, 219, 219, 0.18)", text: "#48dbdb" },
};

export function CoBubbles({ tags }: { tags: number[] }) {
  if (tags.length === 0) return null;
  return (
    <span className="co-bubbles">
      {tags.map((co) => {
        const c = CO_COLORS[co] || { bg: "rgba(255,255,255,0.1)", text: "#ccc" };
        return (
          <span
            key={co}
            className="co-bubble"
            style={{ background: c.bg, color: c.text }}
          >
            {co}
          </span>
        );
      })}
    </span>
  );
}
