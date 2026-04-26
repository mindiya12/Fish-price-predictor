"use client";

import { useMemo, useState } from "react";

type Preset = "1m" | "3m" | "6m" | "1y" | "custom";
export type DateRange = { from: string; to: string };

function isoDate(d: Date) { return d.toISOString().slice(0, 10); }
function addDays(d: Date, days: number) {
  const x = new Date(d); x.setDate(x.getDate() + days); return x;
}

export default function DateRangeSelector({
  onApply,
  initialRange,
}: {
  onApply: (range: DateRange) => void;
  initialRange?: DateRange;
}) {
  const today = useMemo(() => new Date(), []);
  const [preset, setPreset] = useState<Preset>("1m");
  const [from, setFrom] = useState(() => initialRange?.from ?? isoDate(addDays(today, -30)));
  const [to, setTo] = useState(() => initialRange?.to ?? isoDate(today));

  const presets = [
    { key: "1m" as Preset, label: "1 Month" },
    { key: "3m" as Preset, label: "3 Months" },
    { key: "6m" as Preset, label: "6 Months" },
    { key: "1y" as Preset, label: "1 Year" },
    { key: "custom" as Preset, label: "Custom" },
  ];

  const applyPreset = (p: Preset) => {
    setPreset(p);
    if (p === "custom") return;
    const days = p === "1m" ? 30 : p === "3m" ? 90 : p === "6m" ? 180 : 365;
    const nextFrom = isoDate(addDays(today, -days));
    const nextTo = isoDate(today);
    setFrom(nextFrom); setTo(nextTo);
    onApply({ from: nextFrom, to: nextTo });
  };

  const inputStyle = {
    width: '100%',
    padding: '0.625rem 0.875rem',
    borderRadius: '0.5rem',
    background: 'rgba(7, 11, 20, 0.8)',
    border: '1px solid rgba(100, 180, 255, 0.15)',
    color: '#EDF4FF',
    fontSize: '0.875rem',
    outline: 'none',
    marginTop: '0.375rem',
    colorScheme: 'dark' as any,
  };

  return (
    <div>
      {/* Preset pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {presets.map(p => {
          const isActive = preset === p.key;
          return (
            <button
              key={p.key}
              type="button"
              onClick={() => applyPreset(p.key)}
              style={{
                padding: '0.4rem 1rem',
                borderRadius: '999px',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
                border: 'none',
                background: isActive ? 'linear-gradient(135deg, #00B4A0, #00D4FF)' : 'rgba(100, 180, 255, 0.07)',
                color: isActive ? '#070B14' : '#7A9CC9',
                boxShadow: isActive ? '0 0 14px rgba(0, 212, 255, 0.28)' : 'none',
                outline: !isActive ? '1px solid rgba(100, 180, 255, 0.12)' : 'none',
              }}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {preset === "custom" && (
        <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.75rem', alignItems: 'end' }}>
          <label>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4A6285', display: 'block', marginBottom: '0.25rem' }}>From</span>
            <input
              type="date"
              value={from}
              onChange={e => setFrom(e.target.value)}
              style={inputStyle}
            />
          </label>
          <label>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#4A6285', display: 'block', marginBottom: '0.25rem' }}>To</span>
            <input
              type="date"
              value={to}
              onChange={e => setTo(e.target.value)}
              style={inputStyle}
            />
          </label>
          <button
            type="button"
            onClick={() => onApply({ from, to })}
            className="btn-primary"
            style={{ height: '40px', whiteSpace: 'nowrap' }}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
