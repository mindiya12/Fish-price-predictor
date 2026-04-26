"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock } from "lucide-react";

type Props = {
  lastUpdatedIso: string;
  nextUpdateIso: string;
  timeZone?: string;
  locale?: string;
};

function pad2(n: number) { return String(n).padStart(2, "0"); }
function formatCountdown(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${pad2(h)}:${pad2(m)}:${pad2(s)}`;
}

export default function UpdateBadge({
  lastUpdatedIso,
  nextUpdateIso,
  timeZone = "Asia/Colombo",
  locale = "en-US",
}: Props) {
  const lastUpdated = useMemo(() => new Date(lastUpdatedIso), [lastUpdatedIso]);
  const nextUpdate = useMemo(() => new Date(nextUpdateIso), [nextUpdateIso]);
  const [nowMs, setNowMs] = useState<number>(0);

  const timeFormatter = useMemo(() =>
    new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit", hour12: true, timeZone }),
    [locale, timeZone]
  );

  useEffect(() => {
    setNowMs(Date.now());
    const t = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const lastUpdatedText = timeFormatter.format(lastUpdated).replace(/\u202f/g, " ");
  const countdown = nowMs > 0 ? formatCountdown(nextUpdate.getTime() - nowMs) : "--:--:--";

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.875rem',
      background: 'rgba(0, 212, 255, 0.05)',
      border: '1px solid rgba(0, 212, 255, 0.12)',
      borderRadius: '0.625rem',
      padding: '0.5rem 0.875rem',
      flexWrap: 'wrap',
    }}>
      {/* Live dot */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10D9A0', boxShadow: '0 0 6px #10D9A0', flexShrink: 0 }} />
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#10D9A0', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Live</span>
      </div>
      
      <div style={{ width: '1px', height: '14px', background: 'rgba(100, 180, 255, 0.15)' }} />

      <span style={{ fontSize: '0.75rem', color: '#4A6285' }}>
        Updated <span style={{ color: '#7A9CC9', fontWeight: 600 }}>{lastUpdatedText}</span>
      </span>

      <div style={{ width: '1px', height: '14px', background: 'rgba(100, 180, 255, 0.15)' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
        <Clock size={11} color="#4A6285" />
        <span style={{ fontSize: '0.7rem', color: '#4A6285' }}>Refresh in </span>
        <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', fontWeight: 700, color: '#00D4FF' }}>{countdown}</span>
      </div>
    </div>
  );
}
