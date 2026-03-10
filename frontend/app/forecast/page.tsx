"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import FishSelector from "@/components/FishSelector";
import ForecastSummaryCards from "@/components/ForecastSummaryCards";
import ForecastPredictionChart from "@/components/ForecastPredictionChart";
import DetailedForecastTable from "@/components/DetailedForecastTable";
import DownloadActions from "@/components/DownloadActions";
import UpdateBadge from "@/components/UpdateBadge";

import { getLatestForecast } from "@/lib/api";
import { toCsv } from "@/lib/toCsv";

export default function ForecastPage() {
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [lastUpdatedIso, setLastUpdatedIso] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const nextUpdateIso = new Date(new Date().setHours(24, 0, 0, 0)).toISOString();

  useEffect(() => {
    async function loadForecast() {
      try {
        const rawData = await getLatestForecast("balaya", "peliyagoda");

        if (rawData && rawData.dates) {
          const transformedRows = rawData.dates.map((dateStr: string, index: number) => ({
            day: index + 1,
            dateLabel: new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            prediction: Math.round(rawData.blended[index]),
            confidence: rawData.confidence[index] ? Math.round(rawData.confidence[index]) : 30,
            lower: rawData.confidenceLower[index] ? Math.round(rawData.confidenceLower[index]) : null,
            upper: rawData.confidenceUpper[index] ? Math.round(rawData.confidenceUpper[index]) : null,
          }));
          setForecastData(transformedRows);
          setLastUpdatedIso(rawData.forecastDate || new Date().toISOString());
        }
      } catch (error) {
        console.error("Failed to load forecast", error);
      } finally {
        setLoading(false);
      }
    }
    loadForecast();
  }, []);

  const clipboardText = toCsv(
    forecastData.map((d) => ({
      Day: d.day,
      Date: d.dateLabel,
      Prediction: d.prediction,
      Confidence: d.confidence,
      Lower: d.lower ?? "",
      Upper: d.upper ?? "",
    }))
  );

  // We don't have a direct 7-day-only file endpoint in MVP, so we leave these undefined 
  // (the clipboard button will still work perfectly using the local clipboardText)
  const csvUrl = undefined;
  const excelUrl = undefined;

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-brand-neutral">Loading detailed forecast...</div>;
  }

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

      {forecastData.length > 0 ? (
        <>
          <ForecastSummaryCards rows={forecastData} wowPercent={-2.1} />

          <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <h2 className="font-[var(--font-poppins)] text-lg">Prediction chart</h2>
              <UpdateBadge lastUpdatedIso={lastUpdatedIso} nextUpdateIso={nextUpdateIso} />
            </div>

            <ForecastPredictionChart rows={forecastData} />
          </section>

          <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
            <h2 className="mb-3 font-[var(--font-poppins)] text-lg">Detailed table</h2>
            <DetailedForecastTable rows={forecastData} />
          </section>
        </>
      ) : (
        <div className="p-4 text-center text-slate-500">No forecast data available.</div>
      )}

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
