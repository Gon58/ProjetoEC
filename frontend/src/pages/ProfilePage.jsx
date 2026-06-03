import { useEffect, useState } from "react";
import {
  getCurrentUser,
  getSteamProfile,
  getSteamInventory,
  getInventoryPriceChanges,
  logoutSteam,
} from "../services/api";
import InventoryGrid from "../components/InventoryGrid";
import StatCard from "../components/StatCard";

const SECTION_HEADING =
  "text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl";

function ProfilePage() {
  const [steamId, setSteamId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [priceChanges, setPriceChanges] = useState({});
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

        // Match each owned item against our price history (14-day change).
        const names = [
          ...new Set(items.map((i) => i.market_hash_name).filter(Boolean)),
        ];
        if (names.length) {
          try {
            const changes = await getInventoryPriceChanges(names, 14);
            setPriceChanges(changes ?? {});
          } catch {
            setPriceChanges({});
          }
        }
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

  if (error && !profile) {
    return (
      <section className="flex flex-col gap-8 px-8 pb-20 pt-12 md:px-16 lg:px-24">
        <div className="text-center">
          <h2 className={SECTION_HEADING}>Steam Profile</h2>
          <p className="mx-auto mt-4 max-w-3xl text-sm text-slate-400 md:text-base">{error}</p>
        </div>
      </section>
    );
  }

  const tradableCount = inventory.filter((item) => item.tradable).length;
  const marketableCount = inventory.filter((item) => item.marketable).length;

  return (
    <section className="flex flex-col gap-20 pb-20 pt-8 md:gap-24 md:pb-28 md:pt-12">

      {/* Profile banner */}
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className={`mb-10 text-center ${SECTION_HEADING}`}>Steam Profile</h2>

        <div className="relative overflow-hidden border border-slate-800 bg-[#17191A]">
          {/* glow strip */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/70 to-transparent" />
          <div className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full bg-sky-500/10 blur-3xl" />

          <div className="relative flex flex-col items-center gap-6 p-8 sm:flex-row sm:items-center sm:gap-8 md:p-10">
            {loading ? (
              <div className="h-28 w-28 shrink-0 animate-pulse rounded-full bg-slate-700/60 ring-2 ring-sky-400/30" />
            ) : profile?.avatar_full ? (
              <img
                src={profile.avatar_full}
                alt={profile.persona_name}
                className="h-28 w-28 shrink-0 rounded-full object-cover ring-2 ring-sky-400/60 ring-offset-2 ring-offset-[#17191A]"
              />
            ) : (
              <div className="flex h-28 w-28 shrink-0 items-center justify-center rounded-full bg-slate-800 text-xs text-slate-500 ring-2 ring-slate-700">
                Sem avatar
              </div>
            )}

            <div className="flex min-w-0 flex-1 flex-col items-center text-center sm:items-start sm:text-left">
              {loading ? (
                <div className="h-8 w-48 animate-pulse rounded bg-slate-700/60" />
              ) : (
                <h3 className="text-2xl font-bold text-slate-100 md:text-3xl">
                  {profile?.persona_name || "Steam User"}
                </h3>
              )}

              <dl className="mt-3 flex flex-wrap justify-center gap-x-6 gap-y-1 text-sm text-slate-400 sm:justify-start">
                <div className="flex gap-1.5">
                  <dt className="text-slate-500">Real name:</dt>
                  <dd className="text-slate-300">{profile?.real_name || "—"}</dd>
                </div>
                <div className="flex gap-1.5">
                  <dt className="text-slate-500">Steam ID:</dt>
                  <dd className="font-mono text-slate-300">{profile?.steam_id || steamId || "—"}</dd>
                </div>
                <div className="flex gap-1.5">
                  <dt className="text-slate-500">Country:</dt>
                  <dd className="text-slate-300">{profile?.country_code || "—"}</dd>
                </div>
              </dl>

              <div className="mt-5 flex flex-wrap items-center justify-center gap-3 sm:justify-start">
                {profile?.profile_url && (
                  <a
                    href={profile.profile_url}
                    target="_blank"
                    rel="noreferrer"
                    className="border border-sky-200/40 bg-sky-400 px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300"
                  >
                    View on Steam
                  </a>
                )}
                <button
                  type="button"
                  onClick={handleLogout}
                  className="border border-slate-600 px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.08em] text-slate-300 transition-colors hover:border-rose-400 hover:text-rose-400"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="stats-grid mt-10">
          <StatCard title="Steam ID" value={steamId || "—"} loading={loading} />
          <StatCard title="Total de itens" value={totalItems} loading={inventoryLoading} />
          <StatCard title="Tradable" value={tradableCount} loading={inventoryLoading} />
          <StatCard title="Marketable" value={marketableCount} loading={inventoryLoading} />
        </div>
      </section>

      {/* Inventory */}
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className={`mb-4 text-center ${SECTION_HEADING}`}>CS2 Inventory</h2>
        <p className="mx-auto mb-8 max-w-3xl text-center text-sm text-slate-400 md:text-base">
          {inventoryLoading
            ? "Loading inventory…"
            : `${totalItems.toLocaleString()} ${totalItems === 1 ? "item" : "items"} in your Steam account.`}
        </p>

        {inventoryLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="h-60 animate-pulse border border-slate-800 bg-[#17191A]" />
            ))}
          </div>
        ) : (
          <InventoryGrid items={inventory} priceChanges={priceChanges} />
        )}
      </section>

    </section>
  );
}

export default ProfilePage;
