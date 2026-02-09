import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import Toast from "../components/Toast";

export default function SmartSearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [parsed, setParsed] = useState(null);
  const [meta, setMeta] = useState({ cached: false, updated_at: null });
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  const canSearch = query.trim().length >= 3;

  const quickChips = useMemo(
    () => [
      { label: "Hiking essentials (student)", q: "Recommend hiking essentials for a student budget" },
      { label: "Study desk setup", q: "I need a study desk setup under $50" },
      { label: "Cheap HDMI cable", q: "HDMI cable 2m for laptop under $10" },
      { label: "Gym at home", q: "Recommend home workout items for beginners under $30" },
      { label: "Office productivity", q: "Affordable office accessories for productivity under $25" },
    ],
    []
  );

  const runSearch = async (force = false) => {
    if (!canSearch) {
      setToast({
        type: "error",
        title: "Enter more details",
        message: "Type at least 3 characters.",
      });
      return;
    }

    setLoading(true);
    try {
      const params = { q: query, limit: 24 };
      if (force) params.force = 1;

      const r = await api.get(`/ai/smart-search/`, { params });

      setResults(r.data?.results || []);
      setParsed(r.data?.interpreted_query || null);
      setMeta({
        cached: !!r.data?.cached,
        updated_at: r.data?.updated_at || null,
      });

      const count = (r.data?.results || []).length;
      if (count === 0) {
        setToast({
          type: "info",
          title: "No matches",
          message: "Try different wording (add a budget, category, or usage like hiking/study).",
        });
      } else if (force) {
        setToast({
          type: "success",
          title: "Updated",
          message: "Search refreshed with latest AI interpretation.",
        });
      }
    } catch (e) {
      const msg =
        e?.response?.data
          ? typeof e.response.data === "string"
            ? e.response.data
            : JSON.stringify(e.response.data)
          : e?.message || "Unknown error";

      setToast({ type: "error", title: "Smart Search failed", message: msg });
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    // Enter = search, Shift+Enter = newline
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runSearch(false);
    }
  };

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(t);
  }, [toast]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "22px 16px" }}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "end", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ marginTop: 0 }}>Smart Search</h2>
          <div style={{ opacity: 0.8, fontWeight: 700, marginTop: 6 }}>
            Describe what you want in natural language (usage + budget works best).
          </div>
          <div style={{ opacity: 0.7, fontWeight: 700, marginTop: 6 }}>
            Tip: Press <span style={{ fontWeight: 900 }}>Enter</span> to search,{" "}
            <span style={{ fontWeight: 900 }}>Shift+Enter</span> for newline.
          </div>
        </div>

        <button
          onClick={() => runSearch(true)}
          disabled={!canSearch || loading}
          style={{
            padding: "12px 14px",
            borderRadius: 14,
            fontWeight: 900,
            border: "1px solid var(--border)",
            background: "white",
            cursor: !canSearch || loading ? "not-allowed" : "pointer",
          }}
          title="Force refresh (re-run AI)"
        >
          Refresh
        </button>
      </div>

      {/* Quick chips */}
      <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
        {quickChips.map((c) => (
          <button
            key={c.label}
            onClick={() => {
              setQuery(c.q);
              setTimeout(() => runSearch(false), 0);
            }}
            style={{
              padding: "10px 12px",
              borderRadius: 999,
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.85)",
              fontWeight: 900,
              cursor: "pointer",
            }}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Search box */}
      <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder={`e.g. "I’m looking for hiking essentials as a student under $30"`}
          style={{
            flex: 1,
            minWidth: 260,
            padding: 12,
            borderRadius: 14,
            border: "1px solid var(--border)",
            fontWeight: 700,
            resize: "vertical",
            background: "white",
          }}
        />

        <button
          onClick={() => runSearch(false)}
          disabled={!canSearch || loading}
          style={{
            padding: "12px 14px",
            borderRadius: 14,
            fontWeight: 900,
            border: "1px solid var(--border)",
            background: "white",
            cursor: !canSearch || loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {/* Sticky status bar so user sees status even when scrolling */}
      {(loading || results.length > 0 || parsed) && (
        <div
          style={{
            position: "sticky",
            top: 72,
            zIndex: 10,
            marginTop: 14,
            padding: "10px 12px",
            borderRadius: 14,
            border: "1px solid var(--border)",
            background: "rgba(255,255,255,0.92)",
            backdropFilter: "blur(8px)",
            display: "flex",
            justifyContent: "space-between",
            gap: 12,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <div style={{ fontWeight: 900 }}>
            {loading ? "Searching…" : `${results.length} result(s)`}
          </div>
          <div style={{ fontWeight: 800, opacity: 0.75 }}>
            {meta.updated_at ? `Updated: ${String(meta.updated_at)} • ` : ""}
            {meta.cached ? "Loaded from cache" : "Freshly generated"}
          </div>
        </div>
      )}

      {/* Interpreted query (collapsible feel by making it compact) */}
      {parsed ? (
        <div
          style={{
            marginTop: 14,
            padding: 12,
            borderRadius: 14,
            border: "1px solid var(--border)",
            background: "white",
          }}
        >
          <div style={{ fontWeight: 900, marginBottom: 6 }}>AI interpreted your search as</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontWeight: 700, opacity: 0.85 }}>
            {JSON.stringify(parsed, null, 2)}
          </pre>
        </div>
      ) : null}

      {/* Results grid */}
      <div
        style={{
          marginTop: 18,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
        }}
      >
        {results.map((p) => (
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
              <div style={{ fontWeight: 900, opacity: 0.85 }}>Why matched</div>
              <div style={{ marginTop: 6, opacity: 0.8, fontWeight: 700 }}>
                {p.match_summary || "Matched your search intent and keywords."}
              </div>
            </div>
          </div>
        ))}

      </div>
    </div>
  );
}
