import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await login(username, password);
      nav("/recommendations");
    } catch (e2) {
      setErr("Login failed. Check username/password.");
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "28px 16px" }}>
      <h2>Login</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          style={{ padding: 12, borderRadius: 12, border: "1px solid #ddd" }}
        />

        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
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
          Login
        </button>
      </form>
    </div>
  );
}
