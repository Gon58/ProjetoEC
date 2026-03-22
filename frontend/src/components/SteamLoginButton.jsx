import { getSteamLoginUrl } from "../services/api";

function SteamLoginButton() {
  const handleLogin = () => {
    window.location.href = getSteamLoginUrl();
  };

  return (
    <button className="primary-btn" onClick={handleLogin}>
      Login com Steam
    </button>
  );
}

export default SteamLoginButton;