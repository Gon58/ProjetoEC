//import { skins } from "../mocks/skins";
import StatCard from "../components/StatCard";
import SkinTable from "../components/SkinTable";
import axios from "axios";
import { useEffect, useState } from "react";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function DashboardPage() {
  const [skins, setSkins] = useState([]);
  const totalSkins = skins.length;
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

  const fetchSkins = async () => {
    try {
      const response = await axios.get(`${apiUrl}/skins?limit=100`);
      setSkins(response.data);
    } catch (error) {
      console.error("Error fetching skins:", error);
    }
  };

  return (
    <section className="dashboard-page">
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Overview of tracked CS skins and their market prices.</p>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard title="Tracked Skins" value={totalSkins} />
        <StatCard title="Average Price" value={`€${averagePrice.toFixed(2)}`} />
        <StatCard title="Highest Price" value={`€${highestPrice.toFixed(2)}`} />
        <StatCard title="Top Popular Skin" value={mostPopular ? mostPopular.name : "—"} />
      </div>

      <div className="content-card">
        <h3>Market Overview</h3>
        <SkinTable skins={skins} />
      </div>
    </section>
  );
}
