import { createContext, useContext, useMemo, useState } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const username = localStorage.getItem("username");
    const access = localStorage.getItem("access");
    // ✅ only treat as logged-in if token exists too
    return username && access ? { username } : null;
  });

  const login = async (username, password) => {
    try {
      const res = await api.post("/auth/login/", { username, password });

      const access = res.data?.access;
      const refresh = res.data?.refresh;

      if (!access || !refresh) {
        throw new Error("Login failed: missing token(s) in response.");
      }

      localStorage.setItem("access", access);
      localStorage.setItem("refresh", refresh);
      localStorage.setItem("username", username);

      setUser({ username });
      return { ok: true };
    } catch (e) {
      // ensure no stale auth remains
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("username");
      setUser(null);

      const msg =
        e?.response?.data
          ? (typeof e.response.data === "string"
              ? e.response.data
              : JSON.stringify(e.response.data))
          : (e?.message || "Login failed");

      throw new Error(msg);
    }
  };

  const logout = async () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("username");
    localStorage.removeItem("smartshop_chatbot_ui_v2");
    setUser(null);

    // optional but recommended: clear assistant session history on server
    try { await api.post("/assistant/reset/"); } catch {}
  };


  const register = async (username, email, password) => {
    try {
      await api.post("/auth/register/", { username, email, password });
      await login(username, password);
      return { ok: true };
    } catch (e) {
      const msg =
        e?.response?.data
          ? (typeof e.response.data === "string"
              ? e.response.data
              : JSON.stringify(e.response.data))
          : (e?.message || "Registration failed");

      throw new Error(msg);
    }
  };

  const isAuthenticated = !!user && !!localStorage.getItem("access");

  const value = useMemo(
    () => ({ user, isAuthenticated, login, logout, register }),
    [user, isAuthenticated]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
