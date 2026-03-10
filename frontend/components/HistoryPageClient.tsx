"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import FishSelector from "@/components/FishSelector";
import DateRangeSelector, { type DateRange } from "@/components/DateRangeSelector";
import HistoryChart from "@/components/HistoryChart";
import DownloadActions from "@/components/DownloadActions";
import MetricCard from "@/components/MetricCard";

import { toCsv } from "@/lib/toCsv";
import { getHistory, getDownloadUrl } from "@/lib/api";

export interface HistoryPoint {
  dateIso: string;
  dateLabel: string;
  price: number;
}

function defaultRange(): DateRange {
  const today = new Date();
  const to = today.toISOString().slice(0, 10);
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - 30);
  const from = fromDate.toISOString().slice(0, 10);
  return { from, to };
}

function computeStats(rows: HistoryPoint[]) {
  if (!rows.length) {
    return { avg: 0, min: 0, max: 0, range: 0, minDate: "", maxDate: "" };
  }

  let sum = 0;
  let min = rows[0].price;
  let max = rows[0].price;
  let minDate = rows[0].dateIso;
  let maxDate = rows[0].dateIso;

  for (const r of rows) {
    sum += r.price;

    if (r.price < min) {
      min = r.price;
      minDate = r.dateIso;
    }

    if (r.price > max) {
      max = r.price;
      maxDate = r.dateIso;
    }
  }

  const avg = Math.round(sum / rows.length);
  return { avg, min, max, range: max - min, minDate, maxDate };
}

export default function HistoryPageClient() {
  const [range, setRange] = useState<DateRange>(() => defaultRange());
  const [rows, setRows] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  // Re-fetch from backend whenever the date range changes
  useEffect(() => {
    async function fetchHistoricalData() {
      setLoading(true);
      try {
        const rawData = await getHistory(range.from, range.to, "balaya", "peliyagoda");

        if (rawData && rawData.dates) {
          const transformed = rawData.dates.map((dateIso: string, i: number) => ({
            dateIso,
            dateLabel: new Date(dateIso).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            price: Math.round(rawData.prices[i]),
          }));
          setRows(transformed);
        } else {
          setRows([]);
        }
      } catch (error) {
        console.error("Failed to load historical data", error);
        setRows([]);
      } finally {
        setLoading(false);
      }
    }

    fetchHistoricalData();
  }, [range]);

  const stats = computeStats(rows);

  const clipboardText = toCsv(
    rows.map((r) => ({
      Date: r.dateIso,
      Price: r.price,
    }))
  );

  // REAL BACKEND INTEGRATION:
  const csvUrl = getDownloadUrl(range.from, range.to, "csv");
  const excelUrl = getDownloadUrl(range.from, range.to, "excel");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-poppins)] text-2xl">Historical Data</h1>
          <p className="text-sm text-brand-neutral">
            View historical price trends for the selected fish (MVP).
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

      <DateRangeSelector initialRange={range} onApply={setRange} />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Average" value={stats.avg} />
        <MetricCard title="Minimum" value={stats.min} subtitle={stats.minDate ? `On ${stats.minDate}` : undefined} />
        <MetricCard title="Maximum" value={stats.max} subtitle={stats.maxDate ? `On ${stats.maxDate}` : undefined} />
        <MetricCard title="Range" value={stats.range} subtitle="Max - Min" />
      </section>

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <div className="mb-3 flex flex-col gap-1">
          <h2 className="font-[var(--font-poppins)] text-lg">Price trend</h2>
          <p className="text-sm text-brand-neutral">
            {loading ? "Loading data..." : `Showing ${rows.length} days from ${range.from} to ${range.to}.`}
          </p>
        </div>

        {!loading && rows.length > 0 ? (
          <HistoryChart rows={rows} />
        ) : !loading ? (
          <div className="flex h-48 items-center justify-center text-slate-400">No data available for this range.</div>
        ) : (
          <div className="flex h-48 items-center justify-center text-slate-400">Loading...</div>
        )}
      </section>

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <h2 className="mb-3 font-[var(--font-poppins)] text-lg">Download</h2>
        <DownloadActions
          clipboardText={clipboardText}
          csvUrl={csvUrl}
          excelUrl={excelUrl}
          csvLabel="Download history (CSV)"
          excelLabel="Download history (Excel)"
          copyLabel="Copy CSV to clipboard"
        />
      </section>
    </div>
  );
}
