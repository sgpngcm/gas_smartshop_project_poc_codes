export default function Toast({ toast, onClose }) {
  if (!toast) return null;

  const bg = toast.type === "error" ? "#ffecec" : "#eafff0";
  const border = toast.type === "error" ? "#ffb3b3" : "#a7f3c7";
  const color = toast.type === "error" ? "#8a0f0f" : "#0b3b1c";

  return (
    <div
      style={{
        position: "fixed",
        right: 18,
        bottom: 18,
        zIndex: 9999,
        width: "min(420px, calc(100vw - 36px))",
        background: bg,
        border: `1px solid ${border}`,
        color,
        padding: 14,
        borderRadius: 14,
        boxShadow: "0 12px 40px rgba(0,0,0,0.12)",
        display: "flex",
        gap: 10,
        alignItems: "flex-start",
      }}
      role="status"
      aria-live="polite"
    >
      <div style={{ fontWeight: 900, lineHeight: 1.2 }}>
        {toast.title || (toast.type === "error" ? "Error" : "Success")}
        <div style={{ fontWeight: 700, opacity: 0.9, marginTop: 6 }}>
          {toast.message}
        </div>
      </div>

      <button
        onClick={onClose}
        style={{
          marginLeft: "auto",
          border: "none",
          background: "transparent",
          fontSize: 18,
          fontWeight: 900,
          cursor: "pointer",
          color,
          lineHeight: "18px",
        }}
        aria-label="Close notification"
        title="Close"
      >
        ×
      </button>
    </div>
  );
}
