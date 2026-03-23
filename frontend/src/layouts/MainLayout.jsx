import Navbar from "../components/Navbar";

function MainLayout({ children, activePage, setActivePage, steamLoggedIn }) {
  return (
    <div className="app-shell">
      <Navbar
        activePage={activePage}
        setActivePage={setActivePage}
        steamLoggedIn={steamLoggedIn}
      />
      <main className="main-content">{children}</main>
    </div>
  );
}

export default MainLayout;