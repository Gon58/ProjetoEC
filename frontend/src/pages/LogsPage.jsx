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
    <section className="flex flex-col gap-20 pb-20 pt-8 md:gap-24 md:pb-28 md:pt-12">
      <section className="px-8 md:px-16 lg:px-24">
        <h2 className="mb-10 text-center text-3xl font-extrabold uppercase tracking-[0.08em] text-transparent bg-white bg-clip-text md:text-4xl">
          Logs
        </h2>
        <p className="mx-auto max-w-3xl text-center text-sm text-slate-400 md:text-base">
          {isParentLevel
            ? "Recent ingestion and database events."
            : `Children logs for event #${selectedParent.id}.`}
        </p>
      </section>

      <section className="px-8 md:px-16 lg:px-24">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-slate-400">
            Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} items)
          </p>

          <div className="flex items-center gap-3">
            {!isParentLevel && (
              <button
                type="button"
                className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300"
                onClick={handleBackToParents}
              >
                Back to parent logs
              </button>
            )}

            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => goToPage(currentPage - 1)}
              disabled={!pagination.has_prev || loading}
            >
              Previous
            </button>

            <button
              type="button"
              className="cursor-pointer border border-sky-200/40 bg-sky-400 px-6 py-3 text-sm font-semibold uppercase tracking-[0.08em] text-slate-950 transition-all hover:scale-[1.02] hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={() => goToPage(currentPage + 1)}
              disabled={!pagination.has_next || loading}
            >
              Next
            </button>
          </div>
        </div>

        {error && <p className="logs-error mt-6 text-center">{error}</p>}

        <div className="mt-8">
          <div className="table-wrapper border border-slate-800/90 overflow-hidden">
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
        </div>
      </section>
    </section>
  );
}
