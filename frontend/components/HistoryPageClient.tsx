"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BarChart2, Download, TrendingUp, TrendingDown } from "lucide-react";

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
  if (!rows.length) return { avg: 0, min: 0, max: 0, range: 0, minDate: "", maxDate: "" };
  let sum = 0, min = rows[0].price, max = rows[0].price, minDate = rows[0].dateIso, maxDate = rows[0].dateIso;
  for (const r of rows) {
    sum += r.price;
    if (r.price < min) { min = r.price; minDate = r.dateIso; }
    if (r.price > max) { max = r.price; maxDate = r.dateIso; }
  }
  return { avg: Math.round(sum / rows.length), min, max, range: max - min, minDate, maxDate };
}

export default function HistoryPageClient() {
  const [range, setRange] = useState<DateRange>(() => defaultRange());
  const [rows, setRows] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHistoricalData() {
      setLoading(true);
      try {
        const rawData = await getHistory(range.from, range.to, "balaya", "peliyagoda");
        if (rawData?.dates) {
          setRows(rawData.dates.map((dateIso: string, i: number) => ({
            dateIso,
            dateLabel: new Date(dateIso).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            price: Math.round(rawData.prices[i]),
          })));
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
  const clipboardText = toCsv(rows.map((r) => ({ Date: r.dateIso, Price: r.price })));
  const csvUrl = getDownloadUrl(range.from, range.to, "csv");
  const excelUrl = getDownloadUrl(range.from, range.to, "excel");

  // Compute trend for the visible window
  const trend = rows.length > 1 ? (rows[rows.length-1].price > rows[0].price ? 'up' : 'down') : 'neutral';
  const priceDiff = rows.length > 1 ? rows[rows.length-1].price - rows[0].price : 0;
  const pricePct = rows.length > 1 ? ((priceDiff / rows[0].price) * 100).toFixed(1) : '0';

  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      {/* ── PAGE HEADER ── */}
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.5rem' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, rgba(0, 180, 160, 0.2), rgba(0, 212, 255, 0.2))', border: '1px solid rgba(0, 212, 255, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart2 size={18} color="#00D4FF" />
            </div>
            <h1 style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontSize: '1.75rem', fontWeight: 800, margin: 0 }}>
              Historical Data
            </h1>
          </div>
          <p style={{ color: '#4A6285', fontSize: '0.875rem', margin: 0 }}>
            Explore price trends for Balaya · Peliyagoda Fish Market
          </p>
        </div>
        <Link
          href="/"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
            padding: '0.5rem 1rem',
            borderRadius: '0.625rem',
            fontSize: '0.85rem', fontWeight: 500,
            color: '#7A9CC9',
            background: 'rgba(100, 180, 255, 0.06)',
            border: '1px solid rgba(100, 180, 255, 0.1)',
            textDecoration: 'none',
          }}
        >
          <ArrowLeft size={14} /> Back
        </Link>
      </div>

      {/* ── DATE RANGE SELECTOR ── */}
      <div className="glass" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
        <p style={{ fontSize: '0.7rem', fontWeight: 700, color: '#4A6285', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.875rem' }}>Select Date Range</p>
        <DateRangeSelector initialRange={range} onApply={setRange} />
      </div>

      {/* ── STAT CARDS ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <MetricCard title="Average Price" value={stats.avg} subtitle={`Over ${rows.length} days`} accentColor="#00D4FF" />
        <MetricCard
          title="Minimum Price"
          value={stats.min}
          subtitle={stats.minDate ? `On ${stats.minDate}` : undefined}
          accentColor="#10D9A0"
          trend="down"
        />
        <MetricCard
          title="Maximum Price"
          value={stats.max}
          subtitle={stats.maxDate ? `On ${stats.maxDate}` : undefined}
          accentColor="#FFB340"
          trend="up"
        />
        <MetricCard
          title="Price Range"
          value={stats.range}
          unit="Rs."
          subtitle="Max minus Min"
          accentColor="#00B4A0"
        />
      </div>

      {/* ── CHART ── */}
      <section className="glass" style={{ padding: '1.75rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 0.25rem' }}>Price Trend</h2>
            <p style={{ fontSize: '0.78rem', color: '#4A6285', margin: 0 }}>
              {loading ? "Loading data..." : `Showing ${rows.length} days from ${range.from} to ${range.to}`}
            </p>
          </div>
          {!loading && rows.length > 1 && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.375rem 0.875rem',
              borderRadius: '999px',
              fontSize: '0.8rem', fontWeight: 700,
              color: trend === 'up' ? '#10D9A0' : '#FF4F6A',
              background: trend === 'up' ? 'rgba(16, 217, 160, 0.1)' : 'rgba(255, 79, 106, 0.1)',
              border: `1px solid ${trend === 'up' ? 'rgba(16, 217, 160, 0.2)' : 'rgba(255, 79, 106, 0.2)'}`,
            }}>
              {trend === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {trend === 'up' ? '+' : ''}{pricePct}% in period
            </div>
          )}
        </div>

        {loading ? (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem', color: '#4A6285' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', border: '3px solid rgba(0, 212, 255, 0.2)', borderTopColor: '#00D4FF', animation: 'spin 0.8s linear infinite' }} />
            <p style={{ fontSize: '0.875rem' }}>Loading data...</p>
          </div>
        ) : rows.length > 0 ? (
          <HistoryChart rows={rows} />
        ) : (
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4A6285' }}>
            No data available for this date range.
          </div>
        )}
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </section>

      {/* ── DOWNLOAD ── */}
      <section className="glass" style={{ padding: '1.75rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <Download size={18} color="#00D4FF" /> Export Historical Data
          </span>
        </h2>
        <p style={{ fontSize: '0.8rem', color: '#4A6285', marginBottom: '1.25rem' }}>Download the price history for the selected date range.</p>
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
