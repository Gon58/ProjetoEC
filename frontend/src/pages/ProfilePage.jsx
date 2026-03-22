import { useEffect, useState } from "react";
import { getCurrentUser, getSteamProfile, getSteamInventory, logoutSteam } from "../services/api";
import InventoryGrid from "../components/InventoryGrid";
import StatCard from "../components/StatCard";

function ProfilePage() {
  const [steamId, setSteamId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [inventoryLoading, setInventoryLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSteamData() {
      try {
        setLoading(true);
        setError("");

        const me = await getCurrentUser();

        if (!me?.steam_id) {
          setError("Ainda não tens sessão Steam iniciada.");
          return;
        }

        setSteamId(me.steam_id);

        const profileResponse = await getSteamProfile();
        setProfile(profileResponse?.player ?? null);

        const inventoryResponse = await getSteamInventory();
        const items = inventoryResponse?.inventory?.items ?? [];

        setInventory(items);
        setTotalItems(inventoryResponse?.inventory?.total_items ?? items.length);
      } catch (err) {
        setError(err?.response?.data?.detail || "Erro ao carregar perfil Steam.");
      } finally {
        setLoading(false);
        setInventoryLoading(false);
      }
    }

    loadSteamData();
  }, []);

  async function handleLogout() {
    try {
      await logoutSteam();
      window.location.reload();
    } catch {
      setError("Não foi possível terminar sessão.");
    }
  }

  if (loading) {
    return (
      <section className="dashboard-page">
        <div className="page-header">
          <h2>Perfil Steam</h2>
          <p>A carregar dados da conta...</p>
        </div>
      </section>
    );
  }

  if (error && !profile) {
    return (
      <section className="dashboard-page">
        <div className="page-header">
          <h2>Perfil Steam</h2>
          <p>{error}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="dashboard-page">
      <div className="page-header">
        <h2>Perfil Steam</h2>
        <p>Dados reais da tua conta e inventário CS2 vindos do backend.</p>
      </div>

      <div className="profile-card">
        <div className="profile-card-left">
          {profile?.avatar_full ? (
            <img
              src={profile.avatar_full}
              alt={profile.persona_name}
              className="profile-avatar"
            />
          ) : (
            <div className="profile-avatar-placeholder">Sem avatar</div>
          )}
        </div>

        <div className="profile-card-right">
          <h3>{profile?.persona_name || "Steam User"}</h3>
          <p><strong>Nome real:</strong> {profile?.real_name || "—"}</p>
          <p><strong>Steam ID:</strong> {profile?.steam_id || steamId || "—"}</p>
          <p><strong>País:</strong> {profile?.country_code || "—"}</p>

          {profile?.profile_url && (
            <p>
              <a
                href={profile.profile_url}
                target="_blank"
                rel="noreferrer"
                className="profile-link"
              >
                Abrir perfil Steam
              </a>
            </p>
          )}

          <div className="hero-actions">
            <button className="secondary-btn" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard title="Steam ID" value={steamId || "—"} />
        <StatCard title="Total de itens" value={totalItems} />
        <StatCard title="Tradable" value={inventory.filter((item) => item.tradable).length} />
        <StatCard title="Marketable" value={inventory.filter((item) => item.marketable).length} />
      </div>

      {inventoryLoading ? (
        <div className="content-card">
          <h3>Inventário Steam</h3>
          <p>A carregar inventário...</p>
        </div>
      ) : (
        <InventoryGrid items={inventory} />
      )}
    </section>
  );
}

export default ProfilePage;