"use client";

import { useEffect, useMemo, useState } from "react";

type Props = {
  lastUpdatedIso: string;
  nextUpdateIso: string;
  timeZone?: string;
  locale?: string;
};

function pad2(n: number) {
  return String(n).padStart(2, "0");
}

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

  const [nowMs, setNowMs] = useState<number>(() => Date.now());

  const timeFormatter = useMemo(
    () =>
      new Intl.DateTimeFormat(locale, {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
        timeZone,
      }),
    [locale, timeZone]
  );

  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const lastUpdatedText = timeFormatter.format(lastUpdated).replace(/\u202f/g, " ");
  const nextUpdateText = timeFormatter.format(nextUpdate).replace(/\u202f/g, " ");

  const countdown =
    nowMs > 0 ? formatCountdown(nextUpdate.getTime() - nowMs) : "--:--:--";

  return (
    <div className="rounded-lg bg-brand-light px-4 py-2 text-xs ring-1 ring-brand-accent/30">
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-brand-neutral">
        <span>Updated: {lastUpdatedText}</span>
        <span>Next: {nextUpdateText}</span>
        <span className="font-semibold text-brand-primary">Refresh in: {countdown}</span>
      </div>
    </div>
  );
}
