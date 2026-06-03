import { useEffect, useState } from "react";
import axios from "axios";
import StatCard from "../components/StatCard";
import SkinTable from "../components/SkinTable";
import PriceHistoryChart from "../components/PriceHistoryChart";
import { getPriceHistory, getSkinHistory, getSteamMarketSkins } from "../services/api";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";
const MAX_SELECTED = 5;

const BROWSE_SORTS = [
  { key: "price_desc", label: "Price ↓", fn: (a, b) => Number(b.mean_price) - Number(a.mean_price) },
  { key: "price_asc",  label: "Price ↑", fn: (a, b) => Number(a.mean_price) - Number(b.mean_price) },
  { key: "name_asc",   label: "A → Z",   fn: (a, b) => a.name.localeCompare(b.name) },
  { key: "name_desc",  label: "Z → A",   fn: (a, b) => b.name.localeCompare(a.name) },
  { key: "popular",    label: "Popular",  fn: (a, b) => Number(b.quantity_sold) - Number(a.quantity_sold) },
];

const TABLE_SORTS = [
  { key: "price_desc", label: "Price: High → Low", fn: (a, b) => Number(b.mean_price) - Number(a.mean_price) },
  { key: "price_asc",  label: "Price: Low → High", fn: (a, b) => Number(a.mean_price) - Number(b.mean_price) },
  { key: "name_asc",   label: "Name: A → Z",       fn: (a, b) => a.name.localeCompare(b.name) },
  { key: "name_desc",  label: "Name: Z → A",       fn: (a, b) => b.name.localeCompare(a.name) },
  { key: "popular",    label: "Most Popular",       fn: (a, b) => Number(b.quantity_sold) - Number(a.quantity_sold) },
];

// ─── pure async helpers ──────────────────────────────────────────────────────

async function loadDefault(days) {
  const data = await getPriceHistory(MAX_SELECTED, days);
  return {
    history: data,
    skins: data.map((d) => ({ id: d.skin_id, name: d.skin_name })),
  };
}

async function loadForSkins(skins, days) {
  const results = await Promise.all(
    skins.map(async (skin) => {
      try {
        const history = await getSkinHistory(skin.id, days);
        return { skin_id: skin.id, skin_name: skin.name, history: Array.isArray(history) ? history : [] };
      } catch {
        return { skin_id: skin.id, skin_name: skin.name, history: [] };
      }
    })
  );
  return results.filter((r) => r.history.length > 0);
}

// ─── component ───────────────────────────────────────────────────────────────

export default function DashboardPage() {
  // All skins (all sources) — for the market table
  const [skins, setSkins] = useState([]);
  const [isLoadingSkins, setIsLoadingSkins] = useState(true);

  // Steam Market skins with history — for the chart browse panel
  const [steamSkins, setSteamSkins] = useState([]);

  // Chart state
  const [priceHistory, setPriceHistory] = useState([]);
  const [selectedSkins, setSelectedSkins] = useState([]);
  const [isDefaultMode, setIsDefaultMode] = useState(true);
  const [historyDays, setHistoryDays] = useState(30);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Browse panel state (chart section)
  const [browseQuery, setBrowseQuery] = useState("");
  const [browseSort, setBrowseSort] = useState("price_desc");

  // Market table state
  const [tableSort, setTableSort] = useState("price_desc");
  const [currentPage, setCurrentPage] = useState(1);

  // ── derived: market table ─────────────────────────────────────────────────
  const tableSortFn = TABLE_SORTS.find((o) => o.key === tableSort)?.fn ?? TABLE_SORTS[0].fn;
  const sortedSkins = [...skins].sort(tableSortFn);
  const pageSize = 10;
  const totalSkins = skins.length;
  const totalPages = Math.max(1, Math.ceil(totalSkins / pageSize));
  const currentSkins = sortedSkins.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const averagePrice = totalSkins > 0 ? skins.reduce((s, x) => s + Number(x.mean_price), 0) / totalSkins : 0;
  const highestPrice = totalSkins > 0 ? Math.max(...skins.map((x) => Number(x.mean_price))) : 0;
  const mostPopular = totalSkins > 0 ? skins.reduce((a, b) => Number(b.quantity_sold) > Number(a.quantity_sold) ? b : a) : null;

  // ── derived: browse panel ─────────────────────────────────────────────────
  const browseSortFn = BROWSE_SORTS.find((o) => o.key === browseSort)?.fn ?? BROWSE_SORTS[0].fn;
  const selectedIds = new Set(selectedSkins.map((s) => s.id));
  const filteredBrowseSkins = steamSkins
    .filter((s) => !selectedIds.has(s.id))
    .filter((s) => !browseQuery || s.name.toLowerCase().includes(browseQuery.toLowerCase()))
    .sort(browseSortFn)
    .slice(0, 150);

  // ── mount ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    setIsLoadingSkins(true);
    axios
      .get(`${apiUrl}/skins`)
      .then((r) => { setSkins(r.data); setCurrentPage(1); })
      .catch((e) => console.error("load skins error", e))
      .finally(() => setIsLoadingSkins(false));
    getSteamMarketSkins().then(setSteamSkins).catch(() => {});
    refreshDefault(30);
  }, []);

  useEffect(() => {
    if (currentPage > totalPages) setCurrentPage(totalPages);
  }, [currentPage, totalPages]);

  // ── helpers ───────────────────────────────────────────────────────────────

  async function refreshDefault(days) {
    setIsLoadingHistory(true);
    try {
      const { history, skins: chips } = await loadDefault(days);
      setPriceHistory(history);
      setSelectedSkins(chips);
    } catch (e) {
      console.error("refreshDefault error", e);
    } finally {
      setIsLoadingHistory(false);
    }
  }

  async function refreshForSkins(skinsArr, days) {
    setIsLoadingHistory(true);
    try {
      const history = await loadForSkins(skinsArr, days);
      setPriceHistory(history);
    } catch (e) {
      console.error("refreshForSkins error", e);
    } finally {
      setIsLoadingHistory(false);
    }
  }

  // ── event handlers ────────────────────────────────────────────────────────

  function handleDaysChange(days) {
    setHistoryDays(days);
    if (isDefaultMode) refreshDefault(days);
    else refreshForSkins(selectedSkins, days);
  }

  function handleAddSkin(skin) {
    const newSkins = [...selectedSkins, { id: skin.id, name: skin.name }];
    setSelectedSkins(newSkins);
    setIsDefaultMode(false);
    refreshForSkins(newSkins, historyDays);
  }

  function handleRemoveSkin(skinId) {
    const newSkins = selectedSkins.filter((s) => s.id !== skinId);
    setSelectedSkins(newSkins);
    if (newSkins.length === 0) {
      setIsDefaultMode(true);
      refreshDefault(historyDays);
    } else {
      setIsDefaultMode(false);
      refreshForSkins(newSkins, historyDays);
    }
  }

  function handleReset() {
    setIsDefaultMode(true);
    setBrowseQuery("");
    refreshDefault(historyDays);
  }

  function handleTableSortChange(key) {
    setTableSort(key);
    setCurrentPage(1);
  }

  // ── render ────────────────────────────────────────────────────────────────

  return (
    <section className="flex flex-col gap-20 pb-20 pt-8 md:gap-24 md:pb-28 md:pt-12">

      {/* Stats */}
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Dashboard
        </h2>
        <p className="mx-auto max-w-3xl text-center text-sm text-slate-400 md:text-base">
          Overview of tracked CS skins and their market prices.
        </p>
        <div className="mt-10">
          <div className="stats-grid">
            <StatCard title="Tracked Skins" value={totalSkins} loading={isLoadingSkins} />
            <StatCard title="Average Price" value={`€${averagePrice.toFixed(2)}`} loading={isLoadingSkins} />
            <StatCard title="Highest Price" value={`€${highestPrice.toFixed(2)}`} loading={isLoadingSkins} />
            <StatCard title="Top Popular Skin" value={mostPopular ? mostPopular.name : "—"} loading={isLoadingSkins} />
          </div>
        </div>
      </section>

      {/* Price History */}
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-4 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Price History
        </h2>
        <p className="mx-auto mb-8 max-w-3xl text-center text-sm text-slate-400 md:text-base">
          {isDefaultMode
            ? "Mean price evolution of the top 5 most expensive skins over time."
            : `Showing ${selectedSkins.length} selected skin${selectedSkins.length !== 1 ? "s" : ""}.`}
        </p>

        {/* Time range */}
        <div className="mb-8 flex justify-center gap-2">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => handleDaysChange(d)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-widest transition-all ${
                historyDays === d
                  ? "border border-sky-400 bg-sky-400 text-slate-950"
                  : "border border-slate-700 bg-transparent text-slate-400 hover:border-sky-400 hover:text-sky-400"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>

        {/* Selected chips */}
        {selectedSkins.length > 0 && (
          <div className="mb-6 flex flex-wrap justify-center gap-2">
            {selectedSkins.map((skin) => (
              <span
                key={skin.id}
                className="flex items-center gap-1.5 border border-sky-500/40 bg-sky-950/50 px-3 py-1 text-xs text-sky-300"
              >
                <span className="max-w-[200px] truncate">{skin.name}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveSkin(skin.id)}
                  className="ml-1 text-sky-400 hover:text-white transition-colors"
                >
                  ×
                </button>
              </span>
            ))}
            {!isDefaultMode && (
              <button
                type="button"
                onClick={handleReset}
                className="border border-slate-600 px-3 py-1 text-xs text-slate-400 hover:border-slate-300 hover:text-slate-200 transition-colors"
              >
                Reset to top 5
              </button>
            )}
          </div>
        )}

        {/* Chart */}
        <div className="mb-8 border border-slate-800/90 bg-[#17191A] p-6">
          {isLoadingHistory ? (
            <div className="flex h-64 items-center justify-center text-sm text-slate-500">Loading…</div>
          ) : (
            <PriceHistoryChart data={priceHistory} />
          )}
        </div>

        {/* Browse panel */}
        {selectedSkins.length < MAX_SELECTED ? (
          <div className="border border-slate-800 bg-[#17191A]">
            {/* Panel header */}
            <div className="flex flex-col gap-3 border-b border-slate-800 p-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                Add skin to chart
                <span className="ml-2 font-normal normal-case text-slate-600">
                  — {steamSkins.length > 0 ? `${steamSkins.length.toLocaleString()} Steam Market skins with history` : "loading…"}
                </span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {BROWSE_SORTS.map((opt) => (
                  <button
                    key={opt.key}
                    type="button"
                    onClick={() => setBrowseSort(opt.key)}
                    className={`px-3 py-1 text-xs font-semibold uppercase tracking-widest transition-all ${
                      browseSort === opt.key
                        ? "border border-sky-400 bg-sky-400 text-slate-950"
                        : "border border-slate-700 bg-transparent text-slate-400 hover:border-sky-400 hover:text-sky-400"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Search filter */}
            <div className="border-b border-slate-800 px-4 py-3">
              <input
                type="text"
                value={browseQuery}
                onChange={(e) => setBrowseQuery(e.target.value)}
                placeholder="Filter by name…"
                className="w-full border border-slate-700 bg-[#0f172a] px-4 py-2 text-sm text-slate-200 outline-none placeholder:text-slate-500 focus:border-sky-500 transition-colors"
              />
            </div>

            {/* Skin list */}
            <ul className="max-h-64 overflow-y-auto">
              {filteredBrowseSkins.length === 0 ? (
                <li className="px-4 py-6 text-center text-sm text-slate-500">
                  {browseQuery ? `No skins found for "${browseQuery}"` : "Loading skins…"}
                </li>
              ) : (
                filteredBrowseSkins.map((skin) => (
                  <li key={skin.id} className="border-b border-slate-800/60 last:border-0">
                    <button
                      type="button"
                      onClick={() => handleAddSkin(skin)}
                      className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
                    >
                      <span className="truncate pr-4">{skin.name}</span>
                      <span className="shrink-0 text-xs text-slate-500">
                        €{Number(skin.mean_price).toFixed(2)}
                      </span>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        ) : (
          <p className="text-center text-xs text-slate-500">
            Maximum 5 skins selected. Remove one to add another.
          </p>
        )}
      </section>

      {/* Market table */}
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-4 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Market overview
        </h2>
        <p className="mx-auto mb-8 max-w-3xl text-center text-sm text-slate-400 md:text-base">
          {isLoadingSkins ? "Loading…" : `${totalSkins.toLocaleString()} skins tracked across all sources`}
        </p>

        {/* Sort controls */}
        <div className="mb-6 flex flex-wrap justify-center gap-2">
          {TABLE_SORTS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => handleTableSortChange(opt.key)}
              className={`px-4 py-2 text-xs font-semibold uppercase tracking-widest transition-all ${
                tableSort === opt.key
                  ? "border border-sky-400 bg-sky-400 text-slate-950"
                  : "border border-slate-700 bg-transparent text-slate-400 hover:border-sky-400 hover:text-sky-400"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-400">Page {currentPage} of {totalPages}</p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </div>
        <div className="mt-8">
          <SkinTable skins={currentSkins} />
        </div>
      </section>

    </section>
  );
}
