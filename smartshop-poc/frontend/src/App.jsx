import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import LandingPage from "./pages/LandingPage";
import ProductsPage from "./pages/ProductsPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import PurchasesPage from "./pages/PurchasesPage";
import InsightsPage from "./pages/InsightsPage";
import ProtectedRoute from "./auth/ProtectedRoute";
import SmartSearchPage from "./pages/SmartSearchPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import ChatbotView from "./components/ChatbotView";

export default function App() {
  return (
    <div style={{ background: "#fbfbfd", minHeight: "100vh" }}>
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/products/:id" element={<ProductDetailPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/smart-search" element={<SmartSearchPage />} />

        <Route path="/recommendations" element={
          <ProtectedRoute><RecommendationsPage /></ProtectedRoute>
        } />
        <Route path="/purchases" element={
          <ProtectedRoute><PurchasesPage /></ProtectedRoute>
        } />
        <Route path="/insights" element={
          <ProtectedRoute><InsightsPage /></ProtectedRoute>
        } />
      </Routes>
      <ChatbotView />
    </div>
    
  );
}
