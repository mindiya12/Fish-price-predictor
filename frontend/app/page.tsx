"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { TrendingUp, TrendingDown, Minus, BarChart2, Download, ChevronRight, Zap, Shield, Clock } from "lucide-react";

import ForecastTable from "@/components/ForecastTable";
import HistoricalChartSection from "@/components/HistoricalChartSection";
import MetricCard from "@/components/MetricCard";
import UpdateBadge from "@/components/UpdateBadge";
import DownloadCsvButton from "@/components/DownloadCsvButton";
import TodayPriceCard from "@/components/TodayPriceCard";
import { getLatestForecast, getDownloadUrl } from "@/lib/api";

export default function HomePage() {
  const [forecastData, setForecastData] = useState<any[]>([]);
  const [lastUpdatedIso, setLastUpdatedIso] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const nextUpdateIso = new Date(new Date().setHours(24, 0, 0, 0)).toISOString();
  const forecastCsvDownloadUrl = getDownloadUrl("2025-01-01", "2025-12-31", "csv");

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

  const today = forecastData[0];
  const avg3Day = forecastData.length > 0 ? Math.round(forecastData.reduce((s, d) => s + d.prediction, 0) / forecastData.length) : 0;
  const rangeMin = forecastData.length > 0 ? Math.min(...forecastData.map(d => d.prediction)) : 0;
  const rangeMax = forecastData.length > 0 ? Math.max(...forecastData.map(d => d.prediction)) : 0;
  const priceTrend = forecastData.length > 1 ? (forecastData[1].prediction - forecastData[0].prediction > 0 ? 'up' : 'down') : 'neutral';

  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      {/* ── HERO ── */}
      <section style={{ position: 'relative', marginLeft: 'calc(-50vw + 50%)', marginRight: 'calc(-50vw + 50%)', width: '100vw', overflow: 'hidden', marginBottom: '4rem' }}>
        <div style={{ position: 'relative', height: 'clamp(380px, 55vh, 560px)' }}>
          <Image
            src="/hero2.png"
            alt="Fish market in Sri Lanka"
            fill
            priority
            style={{ objectFit: 'cover', objectPosition: '75% 50%' }}
          />
          {/* Multi-layer overlay */}
          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg, rgba(7,11,20,0.92) 0%, rgba(7,11,20,0.65) 50%, rgba(7,11,20,0.4) 100%)' }} />
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 70% 80% at 15% 50%, rgba(0, 180, 160, 0.15) 0%, transparent 70%)' }} />

          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center' }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem', width: '100%' }}>
              <div style={{ maxWidth: '640px' }} className="animate-fade-up">
                {/* Live badge */}
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', background: 'rgba(16, 217, 160, 0.1)', border: '1px solid rgba(16, 217, 160, 0.25)', borderRadius: '999px', padding: '0.35rem 0.875rem' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10D9A0', boxShadow: '0 0 8px #10D9A0' }} className="animate-pulse-ring" />
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#10D9A0', letterSpacing: '0.08em', textTransform: 'uppercase' }}>Live AI Forecast</span>
                </div>

                <div className="animate-hero-float">
                  <h1 style={{ fontSize: 'clamp(2.25rem, 5vw, 3.5rem)', color: '#EDF4FF', marginBottom: '1rem', fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
                    Fish Price{' '}
                    <span style={{ background: 'linear-gradient(135deg, #00D4FF, #10D9A0)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                      Forecast
                    </span>
                  </h1>

                  <p style={{ fontSize: 'clamp(0.95rem, 2vw, 1.15rem)', color: 'rgba(237, 244, 255, 0.75)', marginBottom: '1.5rem', lineHeight: 1.7 }}>
                    AI-powered 3-day price predictions for Balaya at Peliyagoda market.{' '}
                    <span style={{ color: '#00D4FF' }}>Updated daily.</span>
                  </p>

                  {/* Chips */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '2rem' }}>
                    {['XGBoost Model', 'Real-Time Data', '3-Day Horizon'].map(chip => (
                      <span key={chip} style={{
                        padding: '0.35rem 0.875rem',
                        borderRadius: '999px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: 'rgba(237,244,255,0.8)',
                        background: 'rgba(255,255,255,0.08)',
                        border: '1px solid rgba(255,255,255,0.12)',
                        backdropFilter: 'blur(8px)',
                      }}>
                        {chip}
                      </span>
                    ))}
                  </div>

                  <div style={{ display: 'flex', gap: '0.875rem', flexWrap: 'wrap' }}>
                    <Link href="/forecast" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                      View Forecast <ChevronRight size={16} />
                    </Link>
                    <Link href="/history" className="btn-ghost" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                      Historical Data
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Today's price floating card */}
          {today && !loading && (
            <div style={{
              position: 'absolute',
              bottom: '2rem',
              right: 'clamp(1rem, 5vw, 4rem)',
              background: 'rgba(13, 21, 38, 0.85)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              borderRadius: '1rem',
              padding: '1.25rem 1.5rem',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 24px rgba(0, 212, 255, 0.1)',
              minWidth: '200px',
            }}>
              <p style={{ fontSize: '0.65rem', fontWeight: 700, color: '#4A6285', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Tomorrow&apos;s Forecast</p>
              <p style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", fontWeight: 800, fontSize: '2rem', color: '#00D4FF', lineHeight: 1, marginBottom: '0.5rem' }}>
                Rs. {today.prediction.toLocaleString()}
              </p>
              <p style={{ fontSize: '0.75rem', color: '#4A6285' }}>Balaya · Peliyagoda</p>
            </div>
          )}
        </div>
      </section>

      {/* ── METRIC CARDS ── */}
      {forecastData.length > 0 && (
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <TodayPriceCard />
            <MetricCard
              title="Day 1 Forecast"
              value={today.prediction}
              subtitle={`±${today.confidence} Rs`}
              trend={priceTrend as any}
              trendText={priceTrend === 'up' ? 'Trending up' : priceTrend === 'down' ? 'Trending down' : 'Stable'}
              accentColor="#00D4FF"
              icon={<Zap size={14} />}
            />
            <MetricCard
              title="3-Day Average"
              value={avg3Day}
              subtitle="Forecast window"
              accentColor="#00B4A0"
              icon={<BarChart2 size={14} />}
            />
            <MetricCard
              title="Predicted Range"
              value={`${rangeMin}–${rangeMax}`}
              unit="Rs."
              subtitle={`Spread: ${rangeMax - rangeMin} Rs`}
              accentColor="#10D9A0"
              icon={<Shield size={14} />}
            />
            <div className="glass" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <p style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#4A6285', marginBottom: '1rem' }}>Last Updated</p>
              <UpdateBadge lastUpdatedIso={lastUpdatedIso} nextUpdateIso={nextUpdateIso} />
            </div>
          </div>
        </section>
      )}

      {/* ── FORECAST TABLE ── */}
      {forecastData.length > 0 && (
        <section className="glass" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.25rem' }}>3-Day Price Forecast</h2>
              <p style={{ fontSize: '0.8rem', color: '#4A6285' }}>Balaya · Peliyagoda Fish Market</p>
            </div>
            <div style={{ display: 'flex', gap: '0.625rem', alignItems: 'center' }}>
              <Link href="/forecast" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8rem', fontWeight: 600, color: '#00D4FF', textDecoration: 'none', padding: '0.4rem 0.875rem', borderRadius: '0.5rem', background: 'rgba(0, 212, 255, 0.07)', border: '1px solid rgba(0, 212, 255, 0.15)' }}>
                Full Details <ChevronRight size={14} />
              </Link>
            </div>
          </div>
          <ForecastTable rows={forecastData} />
        </section>
      )}

      {/* ── HISTORICAL CHART ── */}
      <section className="glass" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        <HistoricalChartSection fishName="Balaya" location="Peliyagoda" />
      </section>

      {/* ── FEATURES STRIP ── */}
      <section style={{ marginBottom: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        {[
          { icon: Zap, title: 'XGBoost AI Model', desc: 'Trained on 9+ years of market data for highly accurate predictions.', color: '#00D4FF' },
          { icon: Shield, title: 'Confidence Bands', desc: 'Every forecast comes with upper/lower bounds so you can plan around uncertainty.', color: '#10D9A0' },
          { icon: Clock, title: 'Updated at 5 AM', desc: 'Fresh CBSL report data processed daily before market opening time.', color: '#FFB340' },
        ].map(feat => {
          const Icon = feat.icon;
          return (
            <div key={feat.title} className="glass glass-hover" style={{ padding: '1.5rem' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: `${feat.color}15`, border: `1px solid ${feat.color}25`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Icon size={18} color={feat.color} />
              </div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem' }}>{feat.title}</h3>
              <p style={{ fontSize: '0.8rem', color: '#4A6285', lineHeight: 1.7 }}>{feat.desc}</p>
            </div>
          );
        })}
      </section>

      {/* ── ABOUT ── */}
      <section id="about" className="glass" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.75rem' }}>
          About <span style={{ color: '#00D4FF' }}>FishPrice.LK</span>
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#7A9CC9', lineHeight: 1.8, maxWidth: '680px' }}>
          FishPrice.LK uses machine learning to predict Balaya fish prices at the Peliyagoda wholesale market.
          Our XGBoost model is trained on price history, weather data from coastal cities, fuel prices, and
          inflation data — retraining daily for the most up-to-date forecasts.
        </p>
      </section>

      {/* Bottom action bar */}
      <section style={{ display: 'flex', gap: '0.875rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
        <Link href="/forecast" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
          View Full Forecast <ChevronRight size={16} />
        </Link>
        <DownloadCsvButton downloadUrl={forecastCsvDownloadUrl} />
      </section>
    </div>
  );
}
