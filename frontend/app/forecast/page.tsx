import Link from "next/link";

import FishSelector from "@/components/FishSelector";
import ForecastSummaryCards from "@/components/ForecastSummaryCards";
import ForecastPredictionChart from "@/components/ForecastPredictionChart";
import DetailedForecastTable from "@/components/DetailedForecastTable";
import DownloadActions from "@/components/DownloadActions";
import UpdateBadge from "@/components/UpdateBadge";

import { detailedForecast7Days } from "@/lib/dummyDataForecast";
import { toCsv } from "@/lib/toCsv";

export default function ForecastPage() {
  const lastUpdatedIso = "2025-12-27T00:05:00+05:30";
  const nextUpdateIso = "2025-12-28T00:05:00+05:30";

  const clipboardText = toCsv(
    detailedForecast7Days.map((d) => ({
      Day: d.day,
      Date: d.dateLabel,
      Prediction: d.prediction,
      Confidence: d.confidence,
      Lower: d.lower ?? "",
      Upper: d.upper ?? "",
      ChangePercent: d.changePct ?? "",
    }))
  );

  // TODO BACKEND INTEGRATION: set these to real URLs later.
  const csvUrl = undefined;
  const excelUrl = undefined;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-poppins)] text-2xl">Forecast</h1>
          <p className="text-sm text-brand-neutral">
            Prediction details for the selected fish (MVP).
          </p>
        </div>

        <Link
          href="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          ← Back to Home
        </Link>
      </div>

      <FishSelector />

      <ForecastSummaryCards rows={detailedForecast7Days} wowPercent={-2.1} />

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-[var(--font-poppins)] text-lg">Prediction chart</h2>
          <UpdateBadge lastUpdatedIso={lastUpdatedIso} nextUpdateIso={nextUpdateIso} />
        </div>

        <ForecastPredictionChart rows={detailedForecast7Days} />
      </section>

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <h2 className="mb-3 font-[var(--font-poppins)] text-lg">Detailed table</h2>
        <DetailedForecastTable rows={detailedForecast7Days} />
      </section>

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <h2 className="mb-3 font-[var(--font-poppins)] text-lg">Export</h2>
        <DownloadActions
          clipboardText={clipboardText}
          csvUrl={csvUrl}
          excelUrl={excelUrl}
          csvLabel="Download forecast (CSV)"
          excelLabel="Download forecast (Excel)"
          copyLabel="Copy CSV to clipboard"
        />
      </section>
    </div>
  );
}
