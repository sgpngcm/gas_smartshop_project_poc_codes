import { API_BASE } from "../api";
import { Link } from "react-router-dom";

export default function ProductCard({ p, onBuy, isBuying }) {
  const imgSrc = p.image ? `${API_BASE}${p.image}` : "/placeholder-product.png";
  const hasBuy = typeof onBuy === "function";

  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 16,
        overflow: "hidden",
        background: "white",
        boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <Link to={`/products/${p.id}`} style={{ textDecoration: "none", color: "inherit" }}>
        <div style={{ width: "100%", aspectRatio: "1/1", background: "#fafafa", overflow: "hidden" }}>
          <img
            src={imgSrc}
            alt={p.name}
            loading="lazy"
            style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
            onError={(e) => {
              e.currentTarget.src = "/placeholder-product.png";
            }}
          />
        </div>
      </Link>

      <div
        style={{
          padding: 12,
          display: "flex",
          flexDirection: "column",
          gap: 6,
          flex: 1,
          // only reserve extra height when we have a Buy button
          minHeight: hasBuy ? 130 : 0,
        }}
      >
        <Link to={`/products/${p.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div
            title={p.name}
            style={{
              fontWeight: 900,
              lineHeight: 1.2,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
              minHeight: 40,
            }}
          >
            {p.name}
          </div>
        </Link>

        <div
          title={p.category}
          style={{
            opacity: 0.7,
            fontSize: 14,
            fontWeight: 700,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {p.category}
        </div>

        {/* Footer */}
        <div
          style={{
            marginTop: "auto",
            display: "flex",
            alignItems: "center",
            justifyContent: hasBuy ? "space-between" : "flex-start",
            gap: 10,
          }}
        >
          <div style={{ fontWeight: 900, fontSize: 16, whiteSpace: "nowrap" }}>
            ${Number(p.price).toFixed(2)}
          </div>

          {hasBuy ? (
            <button
              onClick={() => onBuy(p.id)}
              disabled={isBuying}
              style={{
                marginLeft: "auto",
                padding: "10px 12px",
                borderRadius: 12,
                border: "none",
                background: isBuying ? "#9db0ff" : "#1f4fff",
                color: "white",
                fontWeight: 900,
                cursor: isBuying ? "not-allowed" : "pointer",
                minWidth: 92,
                height: 40,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
              }}
            >
              {isBuying ? "Buying…" : "Buy"}
            </button>
          ) : (
            <Link
              to={`/products/${p.id}`}
              style={{
                marginLeft: "auto",
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid var(--border)",
                background: "white",
                fontWeight: 900,
                textDecoration: "none",
                color: "#0b1220",
                height: 40,
                display: "flex",
                alignItems: "center",
              }}
            >
              Details
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
