import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr("");

    try {
      await register(username, email, password);
      nav("/products");
    } catch (e2) {
      // show real backend error
      const msg =
        e2?.response?.data
          ? typeof e2.response.data === "string"
            ? e2.response.data
            : JSON.stringify(e2.response.data)
          : e2?.message || "Unknown error";
      setErr(`Registration failed: ${msg}`);
      console.error("Register error:", e2?.response?.status, e2?.response?.data, e2);
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "28px 16px" }}>
      <h2>Register</h2>
      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={{ padding: 12, borderRadius: 12, border: "1px solid #ddd" }}
        />
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email (optional)"
          style={{ padding: 12, borderRadius: 12, border: "1px solid #ddd" }}
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password (min 6 chars)"
          type="password"
          style={{ padding: 12, borderRadius: 12, border: "1px solid #ddd" }}
        />

        {err ? <div style={{ color: "crimson", fontWeight: 800 }}>{err}</div> : null}

        <button
          type="submit"
          style={{
            padding: 12,
            borderRadius: 12,
            border: "none",
            background: "#1f4fff",
            color: "white",
            fontWeight: 900,
            cursor: "pointer",
          }}
        >
          Create Account
        </button>
      </form>
    </div>
  );
}
