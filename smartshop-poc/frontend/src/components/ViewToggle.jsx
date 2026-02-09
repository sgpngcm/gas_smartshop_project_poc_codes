export default function ViewToggle({ value, onChange }) {
  const pill = (active) => ({
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid var(--border)",
    background: active ? "var(--primary)" : "white",
    color: active ? "white" : "var(--text)",
    fontWeight: 900,
    cursor: "pointer",
    userSelect: "none",
  });

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <span style={{ fontWeight: 900, opacity: 0.75 }}>View:</span>

      <button type="button" onClick={() => onChange("grid")} style={pill(value === "grid")}>
        Cards
      </button>

      <button type="button" onClick={() => onChange("list")} style={pill(value === "list")}>
        List
      </button>

      <button type="button" onClick={() => onChange("compact")} style={pill(value === "compact")}>
        Compact
      </button>
    </div>
  );
}
