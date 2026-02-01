// lib/dummyHistory.ts
export type HistoryPoint = {
  dateIso: string;   // "YYYY-MM-DD"
  dateLabel: string; // "Dec 28"
  price: number;     // Rs
};

// Deterministic-ish series for UI.
// TODO BACKEND INTEGRATION: Replace with GET /api/history?from=...&to=...&fish=... [file:635]
export const historyData: HistoryPoint[] = (() => {
  const out: HistoryPoint[] = [];

  const start = new Date();
  start.setDate(start.getDate() - 365);

  let base = 620;

  for (let i = 0; i <= 365; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);

    const weekly = i % 7 === 0 ? -10 : 3;
    const wave = Math.sin(i / 14) * 18;
    const drift = i * 0.03;

    const price = Math.max(450, Math.round(base + weekly + wave + drift));
    base = price;

    const dateIso = d.toISOString().slice(0, 10);
    const dateLabel = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });

    out.push({ dateIso, dateLabel, price });
  }

  return out;
})();
