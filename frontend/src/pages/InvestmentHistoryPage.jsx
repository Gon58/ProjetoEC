import { investments } from "../mocks/investments";

export default function InvestmentHistoryPage() {
  const totalInvestments = investments.length;
  const invested = investments.reduce((sum, item) => sum + item.price_eur * item.quantity, 0);
  const soldCount = investments.filter((item) => item.outcome === "Vendida").length;

  return (
    <section className="dashboard-page">
      <div className="page-header">
        <div>
          <h2>Histórico de Investimentos</h2>
          <p>Registos das compras e vendas de skins de CS, incluindo resultados.</p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-title">Transações</div>
          <div className="stat-value">{totalInvestments}</div>
        </div>
        <div className="stat-card">
          <div className="stat-title">Investido (EUR)</div>
          <div className="stat-value">€{invested.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-title">Vendidas</div>
          <div className="stat-value">{soldCount}</div>
        </div>
      </div>

      <div className="content-card">
        <h3>Histórico do utilizador</h3>
        <div className="table-wrapper">
          <table className="skins-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Skin</th>
                <th>Qualidade</th>
                <th>Qtd</th>
                <th>Preço (EUR)</th>
                <th>Resultado</th>
                <th>Notas</th>
              </tr>
            </thead>
            <tbody>
              {investments.map((item) => (
                <tr key={item.id}>
                  <td>{item.date}</td>
                  <td>{item.skin}</td>
                  <td>{item.quality}</td>
                  <td>{item.quantity}</td>
                  <td>€{item.price_eur.toLocaleString()}</td>
                  <td>{item.outcome}</td>
                  <td>{item.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
