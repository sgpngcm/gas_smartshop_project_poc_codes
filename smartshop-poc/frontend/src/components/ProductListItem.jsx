import { API_BASE } from "../api";

function resolveImageSrc(p) {
  const raw = p?.image_url || p?.image || null;
  if (!raw) return null;
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  const path = raw.startsWith("/") ? raw : `/media/${raw}`;
  return `${API_BASE}${path}`;
}

export default function ProductListItem({ p, onBuy, isBuying }) {
  const imgSrc = resolveImageSrc(p);

  return (
    <div
      style={{
        display: "flex",
        gap: 14,
        padding: 12,
        borderRadius: 16,
        border: "1px solid #eee",
        background: "white",
        boxShadow: "0 10px 30px rgba(0,0,0,0.03)",
        alignItems: "center",
      }}
    >
      <div
        style={{
          width: 86,
          height: 86,
          borderRadius: 14,
          overflow: "hidden",
          background: "#fafafa",
          flex: "0 0 auto",
        }}
      >
        {imgSrc ? (
          <img
            src={imgSrc}
            alt={p.name}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            loading="lazy"
          />
        ) : null}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 950, fontSize: 16, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {p.name}
        </div>
        <div style={{ marginTop: 4, opacity: 0.75, fontWeight: 700 }}>
          {p.category}
        </div>
        <div style={{ marginTop: 8, fontWeight: 950 }}>${p.price}</div>
      </div>

      {onBuy ? (
        <button
          onClick={() => onBuy(p.id)}
          disabled={isBuying}
          style={{
            padding: "10px 12px",
            borderRadius: 12,
            border: "none",
            background: isBuying ? "#9db0ff" : "#1f4fff",
            color: "white",
            fontWeight: 950,
            cursor: isBuying ? "not-allowed" : "pointer",
            minWidth: 92,
          }}
        >
          {isBuying ? "Buying…" : "Buy"}
        </button>
      ) : null}
    </div>
  );
}
