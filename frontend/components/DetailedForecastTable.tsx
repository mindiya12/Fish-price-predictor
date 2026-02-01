import type { ForecastPoint } from "@/types";

function formatChange(pct?: number) {
  if (pct == null || !Number.isFinite(pct)) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function changeColor(pct?: number) {
  if (pct == null) return "text-brand-neutral";
  if (pct > 0) return "text-brand-success";
  if (pct < 0) return "text-brand-alert";
  return "text-brand-neutral";
}

export default function DetailedForecastTable({ rows }: { rows: ForecastPoint[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] table-auto border-separate border-spacing-0 text-sm">
        <thead>
          <tr className="text-left text-slate-600">
            <th className="border-b border-slate-200 px-3 py-2">Day</th>
            <th className="border-b border-slate-200 px-3 py-2">Date</th>
            <th className="border-b border-slate-200 px-3 py-2">Prediction</th>
            <th className="border-b border-slate-200 px-3 py-2">Confidence</th>
            <th className="border-b border-slate-200 px-3 py-2">Change</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((r) => (
            <tr
              key={`${r.day}-${r.dateLabel}`}
              className="odd:bg-white even:bg-brand-light/40 hover:bg-brand-light transition"
            >
              <td className="border-b border-slate-100 px-3 py-2">{r.day}</td>
              <td className="border-b border-slate-100 px-3 py-2">{r.dateLabel}</td>
              <td className="border-b border-slate-100 px-3 py-2 font-medium text-slate-900">
                Rs. {r.prediction}
              </td>
              <td className="border-b border-slate-100 px-3 py-2 text-slate-700">
                ± {r.confidence} Rs
              </td>
              <td className={`border-b border-slate-100 px-3 py-2 font-medium ${changeColor(r.changePct)}`}>
                {formatChange(r.changePct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
