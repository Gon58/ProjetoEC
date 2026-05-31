import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#38bdf8", "#818cf8", "#34d399", "#f472b6", "#fb923c"];

function formatDate(dateStr) {
  const [, month, day] = dateStr.split("-");
  return `${day}/${month}`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="border border-slate-700 bg-[#17191A] px-3 py-2 text-xs text-slate-200 shadow-lg">
      <p className="mb-1 font-semibold text-slate-400">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} style={{ color: entry.color }}>
          {entry.name}: €{Number(entry.value).toFixed(2)}
        </p>
      ))}
    </div>
  );
}

export default function PriceHistoryChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-500">
        Sem dados de histórico disponíveis. Corre o script de mock data.
      </div>
    );
  }

  // Merge all skins into a flat date-keyed array for recharts
  const dateMap = {};
  for (const skinData of data) {
    for (const point of skinData.history) {
      if (!dateMap[point.date]) dateMap[point.date] = { date: formatDate(point.date) };
      dateMap[point.date][skinData.skin_name] = point.mean_price;
    }
  }
  const chartData = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="date"
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: "#334155" }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: "#94a3b8", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `€${v}`}
          width={60}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, color: "#94a3b8", paddingTop: 12 }}
          formatter={(value) => value.length > 35 ? value.slice(0, 32) + "…" : value}
        />
        {data.map((skinData, idx) => (
          <Line
            key={skinData.skin_id}
            type="monotone"
            dataKey={skinData.skin_name}
            stroke={COLORS[idx % COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
