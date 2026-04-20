import { getSteamLoginUrl } from "../services/api";

function SteamLoginButton({ steamLoggedIn, onProfileClick, isProfileActive }) {
  const handleLogin = () => {
    window.location.href = getSteamLoginUrl();
  };

  if (steamLoggedIn) {
    return (
      <button
        className={`cursor-pointer relative bg-transparent px-0 py-0 text-sm transition-colors hover:text-sky-400 ${
          isProfileActive
            ? "text-sky-400 after:absolute after:-bottom-2 after:left-0 after:h-0.5 after:w-full after:bg-sky-500"
            : "text-slate-300"
        }`}
        onClick={onProfileClick}
      >
        Profile
      </button>
    );
  }

  return (
    <button
      className="cursor-pointer border border-sky-500/60 bg-sky-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-sky-400"
      onClick={handleLogin}
    >
      Login with Steam
    </button>
  );
}

export default SteamLoginButton;