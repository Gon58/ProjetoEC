import { useEffect, useState } from "react";
import "./App.css";
import MainLayout from "./layouts/MainLayout";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import InvestmentHistoryPage from "./pages/InvestmentHistoryPage";
import LogsPage from "./pages/LogsPage";
import ProfilePage from "./pages/ProfilePage";
import { getCurrentUser } from "./services/api";

function App() {
  const [activePage, setActivePage] = useState("home");
  const [steamLoggedIn, setSteamLoggedIn] = useState(false);

  useEffect(() => {
    async function checkSteamSession() {
      try {
        const me = await getCurrentUser();
        setSteamLoggedIn(Boolean(me?.steam_id));

        const params = new URLSearchParams(window.location.search);
        if (params.get("steam_login") === "success") {
          setActivePage("profile");
          window.history.replaceState({}, "", window.location.pathname);
        }
      } catch {
        setSteamLoggedIn(false);
      }
    }

    checkSteamSession();
  }, []);

  function renderPage() {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage />;
      case "chat":
        return <ChatPage />;
      case "investments":
        return <InvestmentHistoryPage />;
      case "logs":
        return <LogsPage />;
      case "profile":
        return <ProfilePage />;
      case "home":
      default:
        return <HomePage setActivePage={setActivePage} />;
    }
  }

  return (
    <MainLayout
      activePage={activePage}
      setActivePage={setActivePage}
      steamLoggedIn={steamLoggedIn}
    >
      {renderPage()}
    </MainLayout>
  );
}

export default App;