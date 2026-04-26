"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, BarChart2 } from "lucide-react";
import HistoryChart from "@/components/HistoryChart";
import { getHistory } from "@/lib/api";

export interface HistoryPoint {
  dateIso: string;
  dateLabel: string;
  price: number;
}

export default function HistoricalChartSection({
  fishName = "Balaya",
  location = "Peliyagoda",
}: {
  fishName?: string;
  location?: string;
}) {
  const [rows, setRows] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const toDate = new Date();
        const fromDate = new Date();
        fromDate.setDate(toDate.getDate() - 30);
        const toStr = toDate.toISOString().slice(0, 10);
        const fromStr = fromDate.toISOString().slice(0, 10);
        const rawData = await getHistory(fromStr, toStr, fishName.toLowerCase(), location.toLowerCase());
        if (rawData?.dates) {
          setRows(rawData.dates.map((dateIso: string, i: number) => ({
            dateIso,
            dateLabel: new Date(dateIso).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            price: Math.round(rawData.prices[i]),
          })));
        }
      } catch (error) {
        console.error("Failed to load historical chart", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [fishName, location]);

  const avg = rows.length > 0 ? Math.round(rows.reduce((s, p) => s + p.price, 0) / rows.length) : 0;
  const min = rows.length > 0 ? Math.min(...rows.map(p => p.price)) : 0;
  const max = rows.length > 0 ? Math.max(...rows.map(p => p.price)) : 0;
  const lastPrice = rows.length > 0 ? rows[rows.length - 1].price : 0;
  const prevPrice = rows.length > 1 ? rows[rows.length - 2].price : lastPrice;
  const trend = lastPrice > prevPrice ? 'up' : lastPrice < prevPrice ? 'down' : 'neutral';

  return (
    <div>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.375rem' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(0, 212, 255, 0.1)', border: '1px solid rgba(0, 212, 255, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart2 size={16} color="#00D4FF" />
            </div>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>30-Day Price History</h2>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#4A6285', margin: 0 }}>
            {fishName} · {location} market
          </p>
        </div>

        {/* Stats pills */}
        {!loading && rows.length > 0 && (
          <div style={{ display: 'flex', gap: '0.625rem', flexWrap: 'wrap' }}>
            {[
              { label: 'Avg', value: `Rs. ${avg}` },
              { label: 'Min', value: `Rs. ${min}` },
              { label: 'Max', value: `Rs. ${max}` },
            ].map(stat => (
              <div key={stat.label} style={{
                padding: '0.375rem 0.875rem',
                borderRadius: '999px',
                background: 'rgba(100, 180, 255, 0.05)',
                border: '1px solid rgba(100, 180, 255, 0.1)',
                fontSize: '0.75rem',
              }}>
                <span style={{ color: '#4A6285', marginRight: '0.375rem' }}>{stat.label}</span>
                <span style={{ fontWeight: 700, color: '#EDF4FF' }}>{stat.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', color: '#4A6285' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', border: '3px solid rgba(0, 212, 255, 0.2)', borderTopColor: '#00D4FF', animation: 'spin 0.8s linear infinite' }} />
            <p style={{ fontSize: '0.875rem' }}>Loading price data...</p>
          </div>
        </div>
      ) : rows.length === 0 ? (
        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4A6285' }}>
          No historical data available.
        </div>
      ) : (
        <HistoryChart rows={rows} />
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
