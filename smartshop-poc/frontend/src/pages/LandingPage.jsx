import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "30px 16px" }}>
      <div style={{
        borderRadius: 24,
        padding: 28,
        background: "linear-gradient(135deg, rgba(31,79,255,0.12), rgba(0,0,0,0.02))",
        border: "1px solid #e8ecff"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <img src="/smartshop-logo.png" alt="SmartShop" style={{ width: 64, height: 64, borderRadius: 18 }} />
          <div style={{ flex: 1, minWidth: 260 }}>
            <h1 style={{ margin: 0, fontSize: 34 }}>SmartShop</h1>
            <p style={{ margin: "6px 0 0 0", opacity: 0.75, fontWeight: 600 }}>
              A modern storefront with AI recommendations and explainable shopping insights.
            </p>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <Link to="/products" style={{
              padding: "12px 14px", borderRadius: 14, background: "#1f4fff", color: "white",
              textDecoration: "none", fontWeight: 900
            }}>
              Browse Products
            </Link>
            <Link to="/recommendations" style={{
              padding: "12px 14px", borderRadius: 14, border: "1px solid #cfd7ff", background: "white",
              textDecoration: "none", fontWeight: 900, color: "#1f4fff"
            }}>
              For You (AI)
            </Link>
          </div>
        </div>

        <div style={{ marginTop: 18, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
          {[
            ["Personalized", "Recommendations based on purchase history."],
            ["Explainable AI", "AI insights explain why items fit you."],
            ["Fast Demo", "Seed products + purchases for screenshots."],
          ].map(([title, desc]) => (
            <div key={title} style={{ padding: 16, background: "white", borderRadius: 18, border: "1px solid #eee" }}>
              <div style={{ fontWeight: 900 }}>{title}</div>
              <div style={{ opacity: 0.75, marginTop: 6 }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
