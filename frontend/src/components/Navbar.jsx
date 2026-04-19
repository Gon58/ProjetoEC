import { useLocation, useNavigate } from "react-router-dom";
import SteamLoginButton from "./SteamLoginButton";

function Navbar({ steamLoggedIn }) {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-20 flex w-full items-center justify-between border-b border-[#26292b] bg-[#17191A] px-4 py-4 text-slate-100 sm:px-8">
      <button
        type="button"
        className="cursor-pointer flex items-center gap-3 rounded-none border-0 bg-transparent p-0 text-inherit hover:opacity-90"
        onClick={() => navigate("/")}
        aria-label="Go back to the main page"
      >
        <img
          src="/TeacherBotConnor.png"
          alt="SkinsTeacher"
          className="h-8 w-8 border border-slate-600 object-cover"
        />
        <h1 className="text-[1.15rem] font-bold leading-none">SkinsTeacher</h1>
      </button>

      <div className="flex items-center gap-6 sm:gap-8">
        <button
          className={`cursor-pointer relative bg-transparent px-0 py-0 text-sm transition-colors hover:text-sky-400 ${
            isActive("/dashboard")
              ? "text-sky-400 after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-full after:bg-sky-500"
              : "text-slate-300"
          }`}
          onClick={() => navigate("/dashboard")}
        >
          Dashboard
        </button>

        <button
          className={`cursor-pointer relative bg-transparent px-0 py-0 text-sm transition-colors hover:text-sky-400 ${
            isActive("/logs")
              ? "text-sky-400 after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-full after:bg-sky-500"
              : "text-slate-300"
          }`}
          onClick={() => navigate("/logs")}
        >
          Logs
        </button>

        <button
          className={`cursor-pointer relative bg-transparent px-0 py-0 text-sm transition-colors hover:text-sky-400 ${
            isActive("/chat")
              ? "text-sky-400 after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-full after:bg-sky-500"
              : "text-slate-300"
          }`}
          onClick={() => navigate("/chat")}
        >
          Chat
        </button>

        <SteamLoginButton
          steamLoggedIn={steamLoggedIn}
          onProfileClick={() => navigate("/profile")}
          isProfileActive={isActive("/profile")}
        />
      </div>
    </header>
  );
}

export default Navbar;