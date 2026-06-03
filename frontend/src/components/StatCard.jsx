export default function StatCard({ title, value, loading = false, className = "" }) {
  return (
    <div
      className={`border border-[#1f2937] bg-[#17191A] p-6 shadow-[0_10px_30px_rgba(0,0,0,0.18)] ${className}`}
    >
      <p className="mb-3 text-sm font-medium text-slate-400">{title}</p>
      {loading ? (
        <div className="h-8 w-3/4 animate-pulse rounded bg-slate-700/60" />
      ) : (
        <h3 className="text-2xl font-semibold text-slate-100">{value}</h3>
      )}
    </div>
  );
}
