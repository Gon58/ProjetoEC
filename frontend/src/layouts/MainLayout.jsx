import Navbar from "../components/Navbar";
import { Outlet } from "react-router-dom";

function MainLayout({ steamLoggedIn }) {
  return (
    <div className="app-shell">
      <Navbar steamLoggedIn={steamLoggedIn} />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout;