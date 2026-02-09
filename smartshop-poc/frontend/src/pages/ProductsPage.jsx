import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard";
import ProductListItem from "../components/ProductListItem";
import ViewToggle from "../components/ViewToggle";
import Toast from "../components/Toast";
import { useAuth } from "../auth/AuthContext";

export default function ProductsPage() {
  const { user } = useAuth();

  const [products, setProducts] = useState([]);
  const [q, setQ] = useState("");
  const [toast, setToast] = useState(null);

  // Track loading state per product id
  const [buyingId, setBuyingId] = useState(null);

  // View mode: "grid" | "list" | "compact" (persist)
  const [view, setView] = useState(() => localStorage.getItem("product_view") || "grid");

  // Sort mode (persist)
  // newest | price_asc | price_desc | category
  const [sort, setSort] = useState(() => localStorage.getItem("product_sort") || "newest");

  useEffect(() => {
    localStorage.setItem("product_view", view);
  }, [view]);

  useEffect(() => {
    localStorage.setItem("product_sort", sort);
  }, [sort]);

  useEffect(() => {
    api
      .get("/products/")
      .then((r) => setProducts(r.data || []))
      .catch((e) => {
        setToast({
          type: "error",
          title: "Failed to load products",
          message: e?.message || "Unknown error",
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
  }, []);

  // auto close toast after 3 seconds
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const filteredAndSorted = useMemo(() => {
    const needle = q.toLowerCase().trim();

    let list = products;
    if (needle) {
      list = list.filter((p) =>
        `${p.name} ${p.category}`.toLowerCase().includes(needle)
      );
    }

    // Create a copy before sorting
    const out = [...list];

    if (sort === "price_asc") {
      out.sort((a, b) => Number(a.price) - Number(b.price));
    } else if (sort === "price_desc") {
      out.sort((a, b) => Number(b.price) - Number(a.price));
    } else if (sort === "category") {
      out.sort((a, b) => String(a.category).localeCompare(String(b.category)));
    } else {
      // newest (assumes higher id = newer)
      out.sort((a, b) => Number(b.id) - Number(a.id));
    }

    return out;
  }, [products, q, sort]);

  const buy = async (productId) => {
    if (!user) {
      setToast({
        type: "error",
        title: "Login required",
        message: "Please login to buy and build purchase history for recommendations.",
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    try {
      setBuyingId(productId);
      await api.post("/purchases/buy/", { product_id: productId, quantity: 1 });

      setToast({
        type: "success",
        title: "Purchased",
        message: "Added to your purchase history. Check 'For You' for recommendations.",
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      const msg =
        e?.response?.data
          ? (typeof e.response.data === "string" ? e.response.data : JSON.stringify(e.response.data))
          : (e?.message || "Unknown error");

      setToast({
        type: "error",
        title: "Purchase failed",
        message: msg,
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setBuyingId(null);
    }
  };

  const sortSelectStyle = {
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid var(--border)",
    background: "white",
    fontWeight: 900,
    cursor: "pointer",
  };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "22px 16px" }}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div
        style={{
          display: "flex",
          alignItems: "end",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ minWidth: 260 }}>
          <h2 style={{ marginTop: 0, marginBottom: 6 }}>Products</h2>
          <div style={{ opacity: 0.75, fontWeight: 700 }}>
            Browse items and purchase to generate personalized AI recommendations.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: 10,
            alignItems: "center",
            flex: "1 1 620px",
            justifyContent: "flex-end",
            flexWrap: "wrap",
          }}
        >
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search products..."
            style={{
              padding: 12,
              borderRadius: 12,
              border: "1px solid #ddd",
              minWidth: 260,
              flex: "1 1 320px",
              fontWeight: 700,
            }}
          />

          <select value={sort} onChange={(e) => setSort(e.target.value)} style={sortSelectStyle}>
            <option value="newest">Newest</option>
            <option value="price_asc">Price: Low → High</option>
            <option value="price_desc">Price: High → Low</option>
            <option value="category">Category (A → Z)</option>
          </select>

          <ViewToggle value={view} onChange={setView} />
        </div>
      </div>

      {/* GRID (Cards) */}
      {view === "grid" ? (
        <div
          style={{
            marginTop: 16,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 14,
            alignItems: "stretch",
          }}
        >
          {filteredAndSorted.map((p) => (
            <ProductCard
              key={p.id}
              p={p}
              onBuy={buy}
              isBuying={buyingId === p.id}
            />
          ))}
        </div>
      ) : null}

      {/* LIST */}
      {view === "list" ? (
        <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
          {filteredAndSorted.map((p) => (
            <ProductListItem
              key={p.id}
              p={p}
              onBuy={buy}
              isBuying={buyingId === p.id}
            />
          ))}
        </div>
      ) : null}

      {/* COMPACT (more items per screen) */}
      {view === "compact" ? (
        <div
          style={{
            marginTop: 16,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 10,
            alignItems: "stretch",
          }}
        >
          {filteredAndSorted.map((p) => (
            <div
              key={p.id}
              style={{
                border: "1px solid #eee",
                borderRadius: 14,
                background: "white",
                overflow: "hidden",
                boxShadow: "0 10px 30px rgba(0,0,0,0.03)",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <ProductCard
                p={p}
                onBuy={buy}
                isBuying={buyingId === p.id}
              />
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
