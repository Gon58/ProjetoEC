import { skins } from "../mocks/skins";
import StatCard from "../components/StatCard";
import SkinTable from "../components/SkinTable";

export default function DashboardPage() {
  const totalSkins = skins.length;
  const averagePrice = skins.reduce((sum, skin) => sum + skin.price, 0) / totalSkins;
  const highestPrice = Math.max(...skins.map((skin) => skin.price));
  const mostPopular = skins.reduce((prev, current) =>
    current.popularity > prev.popularity ? current : prev
  );

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
        <StatCard title="Top Popular Skin" value={mostPopular.name} />
      </div>

      <div className="content-card">
        <h3>Market Overview</h3>
        <SkinTable skins={skins} />
      </div>
    </section>
  );
}
