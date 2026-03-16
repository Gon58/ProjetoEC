import { useState } from "react";
import MainLayout from "./layouts/MainLayout";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  const [page, setPage] = useState("home");

  return (
    <MainLayout currentPage={page} onNavigate={setPage}>
      {page === "home" && <HomePage onEnterDashboard={() => setPage("dashboard")} />}
      {page === "dashboard" && <DashboardPage />}
    </MainLayout>
  );
}
