import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import InvestmentHistoryPage from "./pages/InvestmentHistoryPage";
import LogsPage from "./pages/LogsPage";
import ProfilePage from "./pages/ProfilePage";
import { getCurrentUser } from "./services/api";

function AppRoutes() {
  const [steamLoggedIn, setSteamLoggedIn] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    async function checkSteamSession() {
      try {
        const me = await getCurrentUser();
        setSteamLoggedIn(Boolean(me?.steam_id));

        const params = new URLSearchParams(window.location.search);
        if (params.get("steam_login") === "success") {
          navigate("/profile", { replace: true });
        }
      } catch {
        setSteamLoggedIn(false);
      }
    }

    checkSteamSession();
  }, [navigate]);

  return (
    <Routes>
      <Route element={<MainLayout steamLoggedIn={steamLoggedIn} />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/investments" element={<InvestmentHistoryPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;