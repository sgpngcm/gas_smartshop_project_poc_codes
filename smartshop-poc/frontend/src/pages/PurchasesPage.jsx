import { useEffect, useState } from "react";
import { api, API_BASE } from "../api";
import Toast from "../components/Toast";
import { Link } from "react-router-dom";

export default function MyPurchasesPage() {
  const [items, setItems] = useState([]);
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/purchases/me/")
      .then((r) => setItems(r.data || []))
      .catch((e) => {
        const msg =
          e?.response?.data
            ? (typeof e.response.data === "string" ? e.response.data : JSON.stringify(e.response.data))
            : (e?.message || "Unknown error");
        setToast({ type: "error", title: "Failed to load purchases", message: msg });
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "22px 16px" }}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "end", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ marginTop: 0, marginBottom: 6 }}>My Purchases</h2>
          <div style={{ opacity: 0.75, fontWeight: 700 }}>
            Click an item to view details and leave a rating/review.
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ marginTop: 16, opacity: 0.75, fontWeight: 800 }}>Loading…</div>
      ) : null}

      <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
        {items.map((it) => {
          const p = it.product;
          const imgSrc = p?.image ? `${API_BASE}${p.image}` : "/placeholder-product.png";

          return (
            <Link
              key={it.id}
              to={`/products/${p.id}`}
              style={{
                textDecoration: "none",
                color: "inherit",
                border: "1px solid var(--border)",
                borderRadius: 16,
                background: "white",
                boxShadow: "0 10px 30px rgba(0,0,0,0.04)",
                padding: 12,
                display: "flex",
                gap: 12,
                alignItems: "center",
              }}
            >
              <div style={{ width: 72, height: 72, borderRadius: 12, overflow: "hidden", background: "#fafafa" }}>
                <img
                  src={imgSrc}
                  alt={p.name}
                  style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                  onError={(e) => (e.currentTarget.src = "/placeholder-product.png")}
                />
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 900, lineHeight: 1.2 }}>{p.name}</div>
                <div style={{ opacity: 0.7, fontWeight: 700, marginTop: 2 }}>{p.category}</div>
                <div style={{ opacity: 0.65, fontWeight: 700, marginTop: 4 }}>
                  Qty: {it.quantity} • Purchased: {new Date(it.purchase_date).toLocaleString()}
                </div>
              </div>

              <div style={{ fontWeight: 900, whiteSpace: "nowrap" }}>${Number(p.price).toFixed(2)}</div>

              <div
                style={{
                  marginLeft: 10,
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid var(--border)",
                  background: "white",
                  fontWeight: 900,
                  whiteSpace: "nowrap",
                }}
              >
                Review →
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
