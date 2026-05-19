"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BarChart2, Table2, Download, ChevronRight, Zap, Shield, BarChart } from "lucide-react";

import ForecastPredictionChart from "@/components/ForecastPredictionChart";
import DetailedForecastTable from "@/components/DetailedForecastTable";
import ForecastTable from "@/components/ForecastTable";
import DownloadActions from "@/components/DownloadActions";
import UpdateBadge from "@/components/UpdateBadge";
import MetricCard from "@/components/MetricCard";
import WholesaleCalculator from "@/components/WholesaleCalculator";
import PriceAlertForm from "@/components/PriceAlertForm";
import ProcurementReportButton from "@/components/ProcurementReportButton";

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
        if (rawData?.dates) {
          setForecastData(rawData.dates.map((dateStr: string, index: number) => ({
            day: index + 1,
            dateLabel: new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            prediction: Math.round(rawData.blended[index]),
            confidence: rawData.confidence[index] ? Math.round(rawData.confidence[index]) : 30,
            lower: rawData.confidenceLower[index] ? Math.round(rawData.confidenceLower[index]) : null,
            upper: rawData.confidenceUpper[index] ? Math.round(rawData.confidenceUpper[index]) : null,
          })));
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
    forecastData.map((d) => ({ Day: d.day, Date: d.dateLabel, Prediction: d.prediction, Confidence: d.confidence, Lower: d.lower ?? "", Upper: d.upper ?? "" }))
  );

  // Generate client-side CSV download URL
  const csvContent = clipboardText;
  const csvBlob = typeof window !== 'undefined' && forecastData.length > 0
    ? new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    : null;
  const csvUrl = csvBlob ? URL.createObjectURL(csvBlob) : undefined;

  // Generate client-side Excel (TSV) download URL
  const tsvContent = forecastData.length > 0
    ? ['Day\tDate\tPrediction (Rs)\tConfidence (Rs)\tLower\tUpper',
      ...forecastData.map(d => `${d.day}\t${d.dateLabel}\t${d.prediction}\t${d.confidence}\t${d.lower ?? ''}\t${d.upper ?? ''}`)].join('\n')
    : '';
  const excelBlob = typeof window !== 'undefined' && tsvContent
    ? new Blob([tsvContent], { type: 'application/vnd.ms-excel;charset=utf-8;' })
    : null;
  const excelUrl = excelBlob ? URL.createObjectURL(excelBlob) : undefined;

  const today = forecastData[0];
  const avg = forecastData.length > 0 ? Math.round(forecastData.reduce((s, d) => s + d.prediction, 0) / forecastData.length) : 0;
  const rangeMin = forecastData.length > 0 ? Math.min(...forecastData.map(d => d.prediction)) : 0;
  const rangeMax = forecastData.length > 0 ? Math.max(...forecastData.map(d => d.prediction)) : 0;

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: '1.5rem' }}>
        <div style={{ width: '48px', height: '48px', borderRadius: '50%', border: '3px solid rgba(0, 212, 255, 0.2)', borderTopColor: '#00D4FF', animation: 'spin 0.8s linear infinite' }} />
        <p style={{ color: '#4A6285', fontSize: '0.9rem' }}>Loading forecast data...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

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
              Forecast Details
            </h1>
          </div>
          <p style={{ color: '#4A6285', fontSize: '0.875rem', margin: 0 }}>
            3-Day AI Price Prediction · Balaya · Peliyagoda Fish Market
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
            transition: 'all 0.2s',
          }}
        >
          <ArrowLeft size={14} /> Back
        </Link>
      </div>

      {/* ── KPI CARDS ── */}
      {forecastData.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <MetricCard
            title="Day 1 Forecast"
            value={today?.prediction ?? 0}
            subtitle={today ? `±${today.confidence} Rs confidence` : "No data"}
            accentColor="#00D4FF"
            icon={<Zap size={14} />}
          />
          <MetricCard
            title="3-Day Average"
            value={avg ?? 0}
            subtitle="Forecast window avg"
            accentColor="#00B4A0"
            icon={<BarChart size={14} />}
          />
          <MetricCard
            title="Predicted Range"
            value={rangeMin && rangeMax ? `${rangeMin}–${rangeMax}` : "0"}
            unit="Rs."
            subtitle={rangeMin && rangeMax ? `Spread: ${rangeMax - rangeMin} Rs` : "No data"}
            accentColor="#10D9A0"
            icon={<Shield size={14} />}
          />
          <MetricCard
            title="Thisan Kulathilake"
          />
          <div className="glass" style={{ padding: '1.5rem' }}>
            <p style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#4A6285', marginBottom: '0.875rem' }}>Update Status</p>
            <UpdateBadge lastUpdatedIso={lastUpdatedIso} nextUpdateIso={nextUpdateIso} />
          </div>
        </div>
      )}

      <div className="forecast-layout">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* ── CHART SECTION ── */}
          {forecastData.length > 0 && (
            <section className="glass" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 0.25rem' }}>Price Prediction Chart</h2>
                  <p style={{ fontSize: '0.78rem', color: '#4A6285', margin: 0 }}>Confidence band shown in teal</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <div style={{ width: '24px', height: '2px', background: '#00D4FF', borderRadius: '1px' }} />
                    <span style={{ color: '#7A9CC9' }}>Prediction</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <div style={{ width: '16px', height: '10px', background: 'rgba(0, 180, 160, 0.2)', borderRadius: '3px' }} />
                    <span style={{ color: '#7A9CC9' }}>Confidence band</span>
                  </div>
                </div>
              </div>
              <ForecastPredictionChart rows={forecastData} />
            </section>
          )}

          {/* ── VOLUME CALCULATOR ── */}
          {forecastData.length > 0 && (
            <WholesaleCalculator forecast={forecastData} />
          )}

          {/* ── TABLE SECTION ── */}
          {forecastData.length > 0 && (
            <section className="glass" style={{ padding: '1.75rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.5rem' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Table2 size={18} color="#00D4FF" /> Detailed Forecast Table
                </span>
              </h2>
              <ForecastTable rows={forecastData} />
            </section>
          )}
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <PriceAlertForm />

          <div className="glass" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#EDF4FF', marginBottom: '1rem' }}>Intelligence</h3>
            <ProcurementReportButton forecast={forecastData} />
          </div>

          {/* ── EXPORT SECTION ── */}
          <section className="glass" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#EDF4FF', marginBottom: '0.5rem' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                <Download size={18} color="#00D4FF" /> Export Data
              </span>
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#4A6285', marginBottom: '1.25rem' }}>Raw data for planning.</p>
            <DownloadActions
              clipboardText={clipboardText}
              csvUrl={csvUrl}
              excelUrl={excelUrl}
              csvLabel="Download CSV"
              excelLabel="Download Excel"
              copyLabel="Copy CSV"
            />
          </section>
        </aside>
      </div>
    </div>
  );
}
