import type { ForecastPoint } from "@/types";
import MetricCard from "@/components/MetricCard";

type Props = {
  rows: ForecastPoint[];
  wowPercent?: number;
};

export default function ForecastSummaryCards({ rows, wowPercent }: Props) {
  const today = rows[0];

  const avg7Day = Math.round(
    rows.reduce((s, d) => s + d.prediction, 0) / rows.length
  );
  const rangeMin = Math.min(...rows.map((d) => d.prediction));
  const rangeMax = Math.max(...rows.map((d) => d.prediction));
  const range = rangeMax - rangeMin;

  const todayChange = today.changePct ?? 0;
  const todayTrend: "up" | "down" | "neutral" =
    todayChange > 0 ? "up" : todayChange < 0 ? "down" : "neutral";

  const trendTextToday =
    todayTrend === "neutral"
      ? "Stable (0.0%)"
      : `${todayTrend === "up" ? "↑" : "↓"} Stable (${
          todayChange > 0 ? "+" : ""
        }${todayChange.toFixed(1)}%)`;

  const wowTrend: "up" | "down" | "neutral" =
    wowPercent == null
      ? "neutral"
      : wowPercent > 0
      ? "up"
      : wowPercent < 0
      ? "down"
      : "neutral";

  const wowText =
    wowPercent == null
      ? undefined
      : `${wowPercent > 0 ? "↑" : wowPercent < 0 ? "↓" : ""} ${
          wowPercent > 0 ? "+" : ""
        }${wowPercent.toFixed(1)}%`;

  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-2">
      <MetricCard
        title="Today’s forecast"
        value={today.prediction}
        subtitle={`Confidence ± ${today.confidence} Rs`}
        trend={todayTrend}
        trendText={trendTextToday}
      />

      <MetricCard
        title="7-day average"
        value={avg7Day}
        subtitle={wowText ? "vs last week" : undefined}
        trend={wowTrend}
        trendText={wowText}
      />

      <MetricCard
        title="Predicted range"
        value={`${rangeMin} – ${rangeMax}`}
        unit="Rs."
        subtitle={`Range ${range} Rs`}
      />
    </section>
  );
}


/**
 * TODO BACKEND INTEGRATION:
 * On both pages, these props should come from backend forecast payload.
 * Suggested endpoint: GET /api/forecast/latest?fish=balaya&market=peliyagoda
 * Return (example):
 * {
 *   todaysForecast, confidenceToday, avg7Day, rangeMin, rangeMax, range, wowPercent, trendTextToday
 * }
 */
