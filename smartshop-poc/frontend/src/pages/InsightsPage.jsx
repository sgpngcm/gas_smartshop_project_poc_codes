import { useEffect, useState } from "react";
import { api } from "../api";

export default function InsightsPage() {
  const [bullets, setBullets] = useState([]);
  const [meta, setMeta] = useState({ cached: false, updated_at: null });
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/ai/insights/")
      .then((r) => {
        setBullets(r.data?.bullets || []);
        setMeta({ cached: !!r.data?.cached, updated_at: r.data?.updated_at || null });
        setError("");
      })
      .catch((e) => {
        const msg = e?.response?.data ? JSON.stringify(e.response.data) : (e?.message || "Unknown error");
        setError(msg);
      });
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "22px 16px" }}>
      <h2 style={{ marginTop: 0 }}>AI Insights</h2>

      {error ? (
        <div style={{ padding: 14, borderRadius: 14, background: "#fff3f3", border: "1px solid #ffd3d3", fontWeight: 800 }}>
          Failed to load insights: {error}
        </div>
      ) : null}

      <div style={{ marginTop: 10, opacity: 0.75, fontWeight: 700 }}>
        {meta.updated_at ? `Last updated: ${String(meta.updated_at)} • ` : ""}
        {meta.cached ? "Loaded from cache" : "Freshly generated"}
      </div>

      <div style={{
        marginTop: 12,
        border: "1px solid #e8ecff",
        background: "rgba(31,79,255,0.06)",
        borderRadius: 18,
        padding: 16,
      }}>
        {bullets.length === 0 ? (
          <div style={{ fontWeight: 800 }}>No insights available yet.</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.7, fontWeight: 700 }}>
            {bullets.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
}
