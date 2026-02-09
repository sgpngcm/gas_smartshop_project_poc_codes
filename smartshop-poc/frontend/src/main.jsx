import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import App from "./App.jsx";

// ✅ Bootstrap CSS (required for Bootstrap widget styling)
import "bootstrap/dist/css/bootstrap.min.css";

// ✅ Optional: Bootstrap JS bundle (only needed if you use Bootstrap dropdown/modal/collapse)
import "bootstrap/dist/js/bootstrap.bundle.min.js";

import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
