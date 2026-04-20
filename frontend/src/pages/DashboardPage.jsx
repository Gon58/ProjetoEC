//import { skins } from "../mocks/skins";
import StatCard from "../components/StatCard";
import SkinTable from "../components/SkinTable";
import axios from "axios";
import { useEffect, useState } from "react";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function DashboardPage() {
  const [skins, setSkins] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const totalSkins = skins.length;
  const totalPages = Math.max(1, Math.ceil(totalSkins / pageSize));
  const currentSkins = skins.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const averagePrice = totalSkins > 0
    ? skins.reduce((sum, skin) => sum + Number(skin.mean_price), 0) / totalSkins
    : 0;
  const highestPrice = totalSkins > 0
    ? Math.max(...skins.map((skin) => Number(skin.mean_price)))
    : 0;
  const mostPopular = totalSkins > 0
    ? skins.reduce((prev, current) =>
        current.quantity_sold > prev.quantity_sold ? current : prev
      )
    : null;

  useEffect(() => {
    fetchSkins();
  }, []);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  const fetchSkins = async () => {
    try {
      const response = await axios.get(`${apiUrl}/skins?limit=5000`);
      setSkins(response.data);
      setCurrentPage(1);
    } catch (error) {
      console.error("Error fetching skins:", error);
    }
  };

  return (
    <section className="flex flex-col gap-20 pb-20 pt-8 md:gap-24 md:pb-28 md:pt-12">
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Dashboard
        </h2>
        <p className="mx-auto max-w-3xl text-center text-sm text-slate-400 md:text-base">
          Overview of tracked CS skins and their market prices.
        </p>

        <div className="mt-10">
          <div className="stats-grid">
            <StatCard title="Tracked Skins" value={totalSkins} />
            <StatCard title="Average Price" value={`€${averagePrice.toFixed(2)}`} />
            <StatCard title="Highest Price" value={`€${highestPrice.toFixed(2)}`} />
            <StatCard title="Top Popular Skin" value={mostPopular ? mostPopular.name : "—"} />
          </div>
        </div>
      </section>

      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Market overview
        </h2>

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-400">
            Page {currentPage} of {totalPages}
          </p>

          <div className="flex items-center gap-3">
            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
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
