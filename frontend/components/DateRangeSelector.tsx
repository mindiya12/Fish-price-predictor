"use client";

import { useMemo, useState } from "react";

type Preset = "1m" | "3m" | "6m" | "1y" | "custom";

export type DateRange = { from: string; to: string };

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function addDays(d: Date, days: number) {
  const x = new Date(d);
  x.setDate(x.getDate() + days);
  return x;
}

function btnClass(active: boolean) {
  return [
    "rounded-full px-4 py-2 text-sm transition ring-1 ring-black/10",
    active ? "bg-brand-primary text-white" : "bg-white text-slate-700 hover:bg-brand-light",
  ].join(" ");
}

export default function DateRangeSelector({
  onApply,
  initialRange,
}: {
  onApply: (range: DateRange) => void;
  initialRange?: DateRange;
}) {
  const today = useMemo(() => new Date(), []);

  const defaultFrom = isoDate(addDays(today, -30));
  const defaultTo = isoDate(today);

  const [preset, setPreset] = useState<Preset>("1m");
  const [from, setFrom] = useState(() => initialRange?.from ?? defaultFrom);
  const [to, setTo] = useState(() => initialRange?.to ?? defaultTo);

  const applyPreset = (p: Preset) => {
    setPreset(p);
    if (p === "custom") return;

    const days = p === "1m" ? 30 : p === "3m" ? 90 : p === "6m" ? 180 : 365;
    const nextFrom = isoDate(addDays(today, -days));
    const nextTo = isoDate(today);

    setFrom(nextFrom);
    setTo(nextTo);
    onApply({ from: nextFrom, to: nextTo });
  };

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
      <h2 className="font-[var(--font-poppins)] text-lg">Date range</h2>

      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={() => applyPreset("1m")} className={btnClass(preset === "1m")}>
          Last Month
        </button>
        <button type="button" onClick={() => applyPreset("3m")} className={btnClass(preset === "3m")}>
          Last 3 Months
        </button>
        <button type="button" onClick={() => applyPreset("6m")} className={btnClass(preset === "6m")}>
          Last 6 Months
        </button>
        <button type="button" onClick={() => applyPreset("1y")} className={btnClass(preset === "1y")}>
          Last Year
        </button>
        <button type="button" onClick={() => applyPreset("custom")} className={btnClass(preset === "custom")}>
          Custom
        </button>
      </div>

      {preset === "custom" ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3 sm:items-end">
          <label className="block text-sm text-slate-700">
            From
            <input
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            />
          </label>

          <label className="block text-sm text-slate-700">
            To
            <input
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900"
            />
          </label>

          <button
            type="button"
            onClick={() => onApply({ from, to })}
            className="rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white hover:opacity-95"
          >
            Apply
          </button>
        </div>
      ) : null}
    </section>
  );
}
