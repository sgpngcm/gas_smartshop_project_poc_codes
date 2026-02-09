import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const nav = useNavigate();

  const doLogout = () => {
    logout();
    nav("/");
  };

  const item = ({ isActive }) => ({
    padding: "10px 12px",
    borderRadius: 12,
    textDecoration: "none",
    color: isActive ? "white" : "var(--text)",
    background: isActive ? "#1f4fff" : "transparent",
    fontWeight: 800,
    letterSpacing: "-0.01em",
    transition: "background 120ms ease, color 120ms ease",
  });

  const pillBtn = {
    marginLeft: 10,
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid var(--border)",
    background: "white",
    fontWeight: 900,
    cursor: "pointer",
    boxShadow: "0 2px 10px rgba(2, 6, 23, 0.06)",
  };

  return (
    <div
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(255,255,255,0.9)",
        backdropFilter: "blur(10px)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <Link
          to="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            textDecoration: "none",
          }}
        >
          <img
            src="/smartshop-logo.png"
            alt="SmartShop"
            style={{
              width: 36,
              height: 36,
              borderRadius: 12,
              boxShadow: "0 6px 16px rgba(2, 6, 23, 0.12)",
            }}
          />
          <div style={{ fontWeight: 950, color: "var(--text)", letterSpacing: "-0.02em" }}>
            SmartShop
          </div>
        </Link>

        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          <NavLink to="/" style={item}>
            Home
          </NavLink>

          <NavLink to="/products" style={item}>
            Products
          </NavLink>

          {/* ✅ Smart Search link (available to everyone) */}
          <NavLink to="/smart-search" style={item}>
            Smart Search
          </NavLink>

          {user ? (
            <>
              <NavLink to="/recommendations" style={item}>
                For You
              </NavLink>

              <NavLink to="/purchases" style={item}>
                My Purchases
              </NavLink>

              <NavLink to="/insights" style={item}>
                AI Insights
              </NavLink>

              <span
                style={{
                  marginLeft: 10,
                  padding: "8px 10px",
                  borderRadius: 12,
                  background: "rgba(15, 23, 42, 0.06)",
                  fontWeight: 900,
                  color: "var(--text)",
                }}
              >
                Hi, {user.username}
              </span>

              <button onClick={doLogout} style={pillBtn}>
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" style={item}>
                Login
              </NavLink>

              <NavLink to="/register" style={item}>
                Register
              </NavLink>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
