export default function Navbar({ currentPage, onNavigate }) {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="brand-badge">CS</span>
        <div>
          <h1>CS Skins Market</h1>
          <p>Price tracker MVP</p>
        </div>
      </div>

      <nav className="navbar-links">
        <button
          className={currentPage === "home" ? "nav-btn active" : "nav-btn"}
          onClick={() => onNavigate("home")}
        >
          Home
        </button>
        <button
          className={currentPage === "dashboard" ? "nav-btn active" : "nav-btn"}
          onClick={() => onNavigate("dashboard")}
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
          className={currentPage === "chat" ? "nav-btn active" : "nav-btn"}
          onClick={() => onNavigate("chat")}
        >
          Chatbot
        </button>
      </nav>
    </header>
  );
}
