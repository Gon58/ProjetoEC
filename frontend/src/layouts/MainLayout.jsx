import Navbar from "../components/Navbar";

export default function MainLayout({ children, currentPage, onNavigate }) {
  return (
    <div className="app-shell">
      <Navbar currentPage={currentPage} onNavigate={onNavigate} />
      <main className="main-content">{children}</main>
    </div>
  );
}
