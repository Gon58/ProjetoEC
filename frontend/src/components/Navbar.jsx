import SteamLoginButton from "./SteamLoginButton";

function Navbar({ activePage, setActivePage, steamLoggedIn }) {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-badge">EC</div>
        <div>
          <h1>CS2 Market Dashboard</h1>
          <p>Skin analytics, portfolio e Steam integration</p>
        </div>
      </div>

      <div className="navbar-links">
        <button
          className={`nav-btn ${activePage === "home" ? "active" : ""}`}
          onClick={() => setActivePage("home")}
        >
          Home
        </button>

        <button
          className={`nav-btn ${activePage === "dashboard" ? "active" : ""}`}
          onClick={() => setActivePage("dashboard")}
        >
          Dashboard
        </button>

        <button
          className={currentPage === "history" ? "nav-btn active" : "nav-btn"}
          onClick={() => onNavigate("history")}
        >
          Histórico
        </button>
        
        <button
          className={currentPage === "logs" ? "nav-btn active" : "nav-btn"}
          onClick={() => onNavigate("logs")}
        >
          Logs
        </button>

        <button
          className={`nav-btn ${activePage === "chat" ? "active" : ""}`}
          onClick={() => setActivePage("chat")}
        >
          Chat
        </button>

        <button
          className={`nav-btn ${activePage === "profile" ? "active" : ""}`}
          onClick={() => setActivePage("profile")}
        >
          Steam Profile
        </button>

        {!steamLoggedIn && <SteamLoginButton />}
      </div>
    </header>
  );
}

export default Navbar;