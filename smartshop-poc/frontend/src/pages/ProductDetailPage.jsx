import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api, API_BASE } from "../api";
import Toast from "../components/Toast";
import { useAuth } from "../auth/AuthContext";

function Stars({ value = 0 }) {
  const v = Math.round(value * 10) / 10;
  const full = Math.round(v);
  return (
    <span title={`${v} / 5`} style={{ letterSpacing: 1 }}>
      {"★★★★★".split("").map((s, i) => (
        <span key={i} style={{ opacity: i < full ? 1 : 0.25 }}>{s}</span>
      ))}
      <span style={{ marginLeft: 8, fontWeight: 800, opacity: 0.8 }}>{v.toFixed(1)}</span>
    </span>
  );
}

export default function ProductDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();

  const [data, setData] = useState(null);
  const [toast, setToast] = useState(null);
  const [saving, setSaving] = useState(false);

  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  const canReview = !!data?.can_review;

  const load = async () => {
    try {
      const r = await api.get(`/products/${id}/`);
      setData(r.data);

      // preload my_review
      const mine = r.data?.my_review;
      if (mine) {
        setRating(mine.rating ?? 5);
        setTitle(mine.title ?? "");
        setBody(mine.body ?? "");
      }
    } catch (e) {
      const msg =
        e?.response?.data
          ? (typeof e.response.data === "string" ? e.response.data : JSON.stringify(e.response.data))
          : (e?.message || "Unknown error");
      setToast({ type: "error", title: "Failed to load product", message: msg });
    }
  };

  useEffect(() => { load(); }, [id]);

  // auto close toast
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(t);
  }, [toast]);

  const saveReview = async () => {
    if (!user) {
      setToast({ type: "error", title: "Login required", message: "Please login to submit a review." });
      return;
    }
    setSaving(true);
    try {
      await api.post(`/products/${id}/review/`, { rating, title, body });
      setToast({ type: "success", title: "Saved", message: "Your review has been submitted." });
      await load(); // refresh stats + reviews + digest cache signature changes
    } catch (e) {
      const msg =
        e?.response?.data?.detail
          ? e.response.data.detail
          : (e?.message || "Unknown error");
      setToast({ type: "error", title: "Review failed", message: msg });
    } finally {
      setSaving(false);
    }
  };

  if (!data) {
    return (
      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "22px 16px" }}>
        <Toast toast={toast} onClose={() => setToast(null)} />
        <div style={{ opacity: 0.8, fontWeight: 800 }}>Loading…</div>
      </div>
    );
  }

  const imgUrl = data.image ? `${API_BASE}${data.image}` : null;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "22px 16px" }}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: 16, alignItems: "start" }}>
        <div style={{ border: "1px solid var(--border)", borderRadius: 18, overflow: "hidden", background: "white" }}>
          <div style={{ aspectRatio: "1/1", background: "#fafafa" }}>
            {imgUrl ? <img src={imgUrl} alt={data.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
          </div>
        </div>

        <div style={{ border: "1px solid var(--border)", borderRadius: 18, background: "white", padding: 16 }}>
          <div style={{ fontSize: 22, fontWeight: 950 }}>{data.name}</div>
          <div style={{ marginTop: 6, opacity: 0.75, fontWeight: 800 }}>{data.category}</div>

          <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <div style={{ fontSize: 20, fontWeight: 950 }}>${Number(data.price).toFixed(2)}</div>
            <div style={{ fontWeight: 900, opacity: 0.85 }}>
              <Stars value={data.avg_rating || 0} />{" "}
              <span style={{ marginLeft: 10, opacity: 0.8 }}>
                ({data.ratings_count || 0} reviews)
              </span>
            </div>
          </div>

          {data.ai_short_description ? (
            <div style={{ marginTop: 14, padding: 12, borderRadius: 14, background: "rgba(31,79,255,0.06)", border: "1px solid rgba(31,79,255,0.18)" }}>
              <div style={{ fontWeight: 950 }}>About this product</div>
              <div style={{ marginTop: 6, fontWeight: 750, opacity: 0.9 }}>{data.ai_short_description}</div>
            </div>
          ) : null}

          {data.ai_review_digest ? (
            <div style={{ marginTop: 12, padding: 12, borderRadius: 14, background: "#fafafa", border: "1px solid var(--border)" }}>
              <div style={{ fontWeight: 950 }}>AI review highlights</div>
              <div style={{ marginTop: 6, fontWeight: 800, opacity: 0.75, fontSize: 13 }}>
                {data.ai_review_digest.label}
              </div>

              <ul style={{ marginTop: 10 }}>
                {(data.ai_review_digest.highlights || []).map((h, idx) => (
                  <li key={idx} style={{ marginBottom: 6, fontWeight: 800, opacity: 0.85 }}>{h}</li>
                ))}
              </ul>

              {(data.ai_review_digest.sample_reviews || []).length ? (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontWeight: 950 }}>AI-generated sample reviews</div>
                  <div style={{ marginTop: 8, display: "grid", gap: 10 }}>
                    {data.ai_review_digest.sample_reviews.map((r, idx) => (
                      <div key={idx} style={{ border: "1px solid var(--border)", borderRadius: 14, padding: 10, background: "white" }}>
                        <div style={{ fontWeight: 950 }}>{r.title || "Sample review"}</div>
                        <div style={{ marginTop: 4, opacity: 0.85, fontWeight: 800 }}>Rating: {r.rating}/5</div>
                        <div style={{ marginTop: 6, opacity: 0.85, fontWeight: 750 }}>{r.body}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      {/* Real user reviews */}
      <div style={{ marginTop: 16, border: "1px solid var(--border)", borderRadius: 18, background: "white", padding: 16 }}>
        <div style={{ fontWeight: 950, fontSize: 18 }}>User reviews</div>

        <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
          {(data.reviews || []).length ? (
            data.reviews.map((r) => (
              <div key={r.id} style={{ border: "1px solid var(--border)", borderRadius: 14, padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <div style={{ fontWeight: 950 }}>{r.title || "Review"}</div>
                  <div style={{ fontWeight: 900, opacity: 0.85 }}>{r.username} • {r.rating}/5</div>
                </div>
                {r.body ? <div style={{ marginTop: 8, fontWeight: 750, opacity: 0.9 }}>{r.body}</div> : null}
                <div style={{ marginTop: 8, fontWeight: 800, opacity: 0.6, fontSize: 12 }}>
                  Updated: {String(r.updated_at)}
                </div>
              </div>
            ))
          ) : (
            <div style={{ opacity: 0.75, fontWeight: 800 }}>No user reviews yet.</div>
          )}
        </div>
      </div>

      {/* Review form (purchasers only) */}
      <div style={{ marginTop: 16, border: "1px solid var(--border)", borderRadius: 18, background: "white", padding: 16 }}>
        <div style={{ fontWeight: 950, fontSize: 18 }}>Your review</div>

        {!user ? (
          <div style={{ marginTop: 8, opacity: 0.75, fontWeight: 800 }}>
            Please login to write a review.
          </div>
        ) : !canReview ? (
          <div style={{ marginTop: 8, opacity: 0.75, fontWeight: 800 }}>
            You can only review items you have purchased.
          </div>
        ) : (
          <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
            <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
              <label style={{ fontWeight: 900 }}>Rating</label>
              <select
                value={rating}
                onChange={(e) => setRating(Number(e.target.value))}
                style={{ padding: 10, borderRadius: 12, border: "1px solid var(--border)", fontWeight: 900 }}
              >
                {[5,4,3,2,1].map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>

            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title (optional)"
              style={{ padding: 12, borderRadius: 12, border: "1px solid var(--border)", fontWeight: 800 }}
            />

            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={4}
              placeholder="Share what you liked, what could be better… (optional)"
              style={{ padding: 12, borderRadius: 12, border: "1px solid var(--border)", fontWeight: 800, resize: "vertical" }}
            />

            <button
              onClick={saveReview}
              disabled={saving}
              style={{ padding: "12px 14px", borderRadius: 14, fontWeight: 950 }}
            >
              {saving ? "Saving…" : "Save review"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
