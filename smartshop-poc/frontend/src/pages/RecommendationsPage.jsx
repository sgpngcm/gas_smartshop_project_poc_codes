import { useEffect, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import Toast from "../components/Toast";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";

export default function RecommendationsPage() {
  const [recs, setRecs] = useState([]);
  const [count, setCount] = useState(0);
  const [meta, setMeta] = useState({ cached: false, updated_at: null });
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const { user } = useAuth();
  const nav = useNavigate();

  const load = async (force = false) => {
    setLoading(true);
    try {
      const url = force ? "/ai/recommendations/?force=1" : "/ai/recommendations/";
      const r = await api.get(url);

      setRecs(r.data?.recommended || []);
      setCount(r.data?.purchase_count || 0);
      setMeta({ cached: !!r.data?.cached, updated_at: r.data?.updated_at || null });

      if (force) {
        setToast({ type: "success", title: "Updated", message: "Recommendations refreshed." });
      }
    } catch (e) {
      const msg =
        e?.response?.data
          ? (typeof e.response.data === "string" ? e.response.data : JSON.stringify(e.response.data))
          : (e?.message || "Unknown error");
      setToast({ type: "error", title: "Failed to load recommendations", message: msg });
    } finally {
      setLoading(false);
    }
  };

useEffect(() => {
  const token = localStorage.getItem("access");

  if (!user || !token) {
    nav("/login");
    return;
  }
  load(false);
}, [user, nav]);

  // auto close toast
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
          <h2 style={{ marginTop: 0 }}>For You</h2>
          <div style={{ opacity: 0.75, fontWeight: 700 }}>
            Recommendations based on your purchase history (purchases: {count}).
          </div>
          <div style={{ opacity: 0.7, fontWeight: 700, marginTop: 6 }}>
            {meta.updated_at ? `Last updated: ${String(meta.updated_at)} • ` : ""}
            {meta.cached ? "Loaded from cache" : "Freshly generated"}
          </div>
        </div>

        <button
          onClick={() => load(true)}
          style={{
            padding: "12px 14px",
            borderRadius: 12,
            border: "1px solid #ddd",
            background: "white",
            fontWeight: 900,
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ marginTop: 16, opacity: 0.75, fontWeight: 800 }}>
          Loading recommendations…
        </div>
      ) : null}

      <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
        {recs.map((p) => (
          <div
            key={p.id}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 10,
              height: "100%",
            }}
          >
            <div style={{ flex: 1 }}>
              <ProductCard p={p} />
            </div>

            <div style={{ padding: 10, borderRadius: 12, border: "1px solid #eee", background: "white" }}>
              <div style={{ fontWeight: 900, opacity: 0.85 }}>Why recommended</div>
              <div style={{ marginTop: 6, opacity: 0.8, fontWeight: 700 }}>
                {p.reason || "Recommended based on your shopping patterns."}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
