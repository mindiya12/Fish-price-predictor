"use client";

import { useEffect, useState } from "react";
import { TrendingUp, AlertCircle, Zap } from "lucide-react";
import { getTodayPrice } from "@/lib/api";
import AnimatedNumber from "./AnimatedNumber";

interface TodayPrice {
  date: string;
  price: number | null;
  type: "actual" | "forecast" | null;
  confLower?: number;
  confUpper?: number;
  fish: string;
  location: string;
}

export default function TodayPriceCard() {
  const [todayPrice, setTodayPrice] = useState<TodayPrice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadTodayPrice() {
      try {
        const data = await getTodayPrice("balaya", "peliyagoda");
        setTodayPrice(data);
      } catch (err) {
        console.error("Failed to load today's price", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    loadTodayPrice();
  }, []);

  if (loading) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(16, 217, 160, 0.08))',
        border: '1px solid rgba(0, 212, 255, 0.2)',
        borderRadius: '1rem',
        padding: '1.5rem',
        backdropFilter: 'blur(4px)',
      }}>
        <div style={{ height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite', color: 'rgba(237, 244, 255, 0.6)' }}>
            Loading today's price...
          </div>
        </div>
      </div>
    );
  }

  if (error || !todayPrice?.price) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(239, 68, 68, 0.04))',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        borderRadius: '1rem',
        padding: '1.5rem',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
      }}>
        <AlertCircle style={{ width: '24px', height: '24px', color: 'rgba(239, 68, 68, 0.8)', flexShrink: 0 }} />
        <div style={{ color: 'rgba(237, 244, 255, 0.7)' }}>
          No price data available for today
        </div>
      </div>
    );
  }

  const isActual = todayPrice.type === "actual";
  const gradient = isActual
    ? "linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05))"
    : "linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(16, 217, 160, 0.08))";

  const borderColor = isActual ? "rgba(34, 197, 94, 0.25)" : "rgba(0, 212, 255, 0.2)";
  const badgeColor = isActual ? "#22C55E" : "#00D4FF";
  const badgeBg = isActual ? "rgba(34, 197, 94, 0.15)" : "rgba(0, 212, 255, 0.15)";

  return (
    <div style={{
      background: gradient,
      border: `1px solid ${borderColor}`,
      borderRadius: '1rem',
      padding: '1.5rem',
      backdropFilter: 'blur(4px)',
    }}>
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          {isActual ? (
            <Zap style={{ width: '18px', height: '18px', color: '#22C55E' }} />
          ) : (
            <TrendingUp style={{ width: '18px', height: '18px', color: '#00D4FF' }} />
          )}
          <span style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '999px',
            fontSize: '0.7rem',
            fontWeight: 700,
            color: badgeColor,
            background: badgeBg,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}>
            {isActual ? "Today's Price" : "Today's Forecast"}
          </span>
        </div>
        <h3 style={{
          fontSize: '0.875rem',
          color: 'rgba(237, 244, 255, 0.7)',
          fontWeight: 500,
          margin: 0,
        }}>
          Balaya at Peliyagoda
        </h3>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', marginBottom: '0.75rem' }}>
        <span style={{
          fontSize: '2.5rem',
          fontWeight: 700,
          color: '#EDF4FF',
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          letterSpacing: '-0.02em',
        }}>
          <AnimatedNumber value={Math.round(todayPrice.price)} />
        </span>
        <span style={{ color: 'rgba(237, 244, 255, 0.6)', fontSize: '1rem', fontWeight: 500 }}>
          Rs
        </span>
      </div>

      {todayPrice.confLower !== undefined && todayPrice.confUpper !== undefined && (
        <div style={{
          fontSize: '0.8rem',
          color: 'rgba(237, 244, 255, 0.5)',
          fontStyle: 'italic',
        }}>
          Range: {Math.round(todayPrice.confLower)} - {Math.round(todayPrice.confUpper)} Rs
        </div>
      )}
    </div>
  );
}
