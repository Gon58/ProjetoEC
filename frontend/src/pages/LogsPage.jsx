import { logs } from "../mocks/logs";

export default function LogsPage() {
  return (
    <section className="dashboard-page">
      <div className="page-header">
        <div>
          <h2>Logs</h2>
          <p>Recent ingestion and database events.</p>
        </div>
      </div>

      <div className="content-card">
        <h3>Event logs</h3>
        <div className="table-wrapper">
          <table className="skins-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Source</th>
                <th>Database</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.timestamp}</td>
                  <td>{log.source}</td>
                  <td>{log.database}</td>
                  <td>{log.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
