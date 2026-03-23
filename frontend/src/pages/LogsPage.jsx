import { useEffect, useState } from "react";

import { getLogs } from "../services/api";

export default function LogsPage() {
  const [selectedParent, setSelectedParent] = useState(null);
  const [logs, setLogs] = useState([]);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 5,
    total_items: 0,
    total_pages: 1,
    has_prev: false,
    has_next: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const currentPage = pagination.page;
  const pageSize = pagination.page_size;

  useEffect(() => {
    async function loadLogs() {
      setLoading(true);
      setError("");

      try {
        const response = await getLogs({
          parentId: selectedParent?.id ?? null,
          page: currentPage,
          pageSize,
        });

        setLogs(response.items ?? []);
        setPagination(response.pagination ?? pagination);
      } catch {
        setError("Failed to load logs.");
      } finally {
        setLoading(false);
      }
    }

    loadLogs();
  }, [selectedParent, currentPage, pageSize]);

  function handleParentClick(log) {
    if (!log.has_children) {
      return;
    }

    setSelectedParent(log);
    setPagination((prev) => ({
      ...prev,
      page: 1,
    }));
  }

  function handleBackToParents() {
    setSelectedParent(null);
    setPagination((prev) => ({
      ...prev,
      page: 1,
    }));
  }

  function goToPage(nextPage) {
    setPagination((prev) => ({
      ...prev,
      page: nextPage,
    }));
  }

  const isParentLevel = !selectedParent;

  return (
    <section className="dashboard-page">
      <div className="page-header">
        <div>
          <h2>Logs</h2>
          <p>
            {isParentLevel
              ? "Recent ingestion and database events."
              : `Children logs for event #${selectedParent.id}.`}
          </p>
        </div>
      </div>

      <div className="content-card">
        <div className="logs-toolbar">
          <h3>{isParentLevel ? "Parent event logs" : "Children event logs"}</h3>
          {!isParentLevel && (
            <button className="secondary-btn" onClick={handleBackToParents}>
              Back to parent logs
            </button>
          )}
        </div>

        {error && <p className="logs-error">{error}</p>}

        <div className="table-wrapper">
          <table className="skins-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                {!isParentLevel && <th>Step</th>}
                <th>Source</th>
                <th>Database</th>
                <th>Description</th>
                {isParentLevel && <th>Children</th>}
              </tr>
            </thead>
            <tbody>
              {!loading && logs.length === 0 && (
                <tr>
                  <td colSpan={isParentLevel ? 5 : 5}>No logs found for this page.</td>
                </tr>
              )}

              {loading && (
                <tr>
                  <td colSpan={isParentLevel ? 5 : 5}>Loading logs...</td>
                </tr>
              )}

              {!loading &&
                logs.map((log) => (
                  <tr
                    key={log.id}
                    className={isParentLevel && log.has_children ? "log-row-clickable" : ""}
                    onClick={
                      isParentLevel && log.has_children
                        ? () => handleParentClick(log)
                        : undefined
                    }
                  >
                    <td>{log.timestamp}</td>
                    {!isParentLevel && <td>{log.step}</td>}
                    <td>{log.source}</td>
                    <td>{log.database}</td>
                    <td>{log.description}</td>
                    {isParentLevel && <td>{log.children_count}</td>}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="logs-pagination">
          <button
            className="secondary-btn"
            onClick={() => goToPage(currentPage - 1)}
            disabled={!pagination.has_prev || loading}
          >
            Previous
          </button>

          <span>
            Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} items)
          </span>

          <button
            className="secondary-btn"
            onClick={() => goToPage(currentPage + 1)}
            disabled={!pagination.has_next || loading}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
