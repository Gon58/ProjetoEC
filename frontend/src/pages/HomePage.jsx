export default function HomePage({ onEnterDashboard }) {
  return (
    <section className="hero">
      <div className="hero-text">
        <span className="hero-tag">MVP</span>
        <h2>Track CS skin prices in a simple and visual way</h2>
        <p>
          This project helps explore and present CS skin market data, including
          current prices, popularity, rarity, and trend indicators.
        </p>

        <div className="hero-actions">
          <button className="primary-btn" onClick={onEnterDashboard}>
            Open Dashboard
          </button>
          <button className="secondary-btn">Learn More</button>
        </div>
      </div>

      <div className="hero-card">
        <h3>What this MVP shows</h3>
        <ul>
          <li>Current skin prices</li>
          <li>Simple market statistics</li>
          <li>Quick overview of popular items</li>
          <li>Clean interface ready to connect to FastAPI</li>
        </ul>
      </div>
    </section>
  );
}
