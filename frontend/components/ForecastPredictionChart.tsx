"use client";

import type { ForecastPoint } from "@/types";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

type Props = { rows: ForecastPoint[] };

export default function ForecastPredictionChart({ rows }: Props) {
  const labels = rows.map((d) => d.dateLabel);
  const prediction = rows.map((d) => d.prediction);

  const hasBand = rows.every((d) => typeof d.lower === "number" && typeof d.upper === "number");
  const lower = hasBand ? rows.map((d) => d.lower as number) : undefined;
  const upper = hasBand ? rows.map((d) => d.upper as number) : undefined;

  const datasets: any[] = [];

  if (hasBand && lower && upper) {
    datasets.push(
      {
        label: "Upper",
        data: upper,
        borderColor: "transparent",
        backgroundColor: "transparent",
        pointRadius: 0,
        fill: false,
      },
      {
        label: "Lower",
        data: lower,
        borderColor: "transparent",
        pointRadius: 0,
        fill: "-1",
        backgroundColor: "rgba(0, 180, 160, 0.12)",
      }
    );
  }

  datasets.push({
    label: "Predicted Price",
    data: prediction,
    borderColor: "#00D4FF",
    backgroundColor: (context: any) => {
      const ctx = context.chart.ctx;
      const gradient = ctx.createLinearGradient(0, 0, 0, 280);
      gradient.addColorStop(0, "rgba(0, 212, 255, 0.2)");
      gradient.addColorStop(1, "rgba(0, 212, 255, 0)");
      return gradient;
    },
    tension: 0.4,
    pointRadius: 5,
    pointHoverRadius: 8,
    pointBackgroundColor: "#00D4FF",
    pointBorderColor: "#070B14",
    pointBorderWidth: 2,
    fill: hasBand ? false : true,
    borderWidth: 2.5,
  });

  const data = { labels, datasets };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      legend: {
        labels: {
          filter: (item) => item.text === "Predicted Price",
          color: "#7A9CC9",
          font: { size: 12 },
        },
      },
      tooltip: {
        intersect: false,
        mode: "index",
        backgroundColor: "rgba(13, 21, 38, 0.95)",
        borderColor: "rgba(0, 212, 255, 0.2)",
        borderWidth: 1,
        titleColor: "#7A9CC9",
        bodyColor: "#EDF4FF",
        bodyFont: { weight: "bold" as any, size: 14 },
        padding: 12,
        callbacks: {
          label: (ctx) => {
            if (ctx.dataset.label === "Predicted Price" && ctx.parsed.y != null) return `  Rs. ${ctx.parsed.y.toLocaleString()}`;
            return "";
          },
          labelColor: (ctx) => ({
            borderColor: "#00D4FF",
            backgroundColor: "#00D4FF",
            borderRadius: 3,
          }),
        },
      },
    },
    scales: {
      y: {
        grid: { color: "rgba(100, 180, 255, 0.05)" },
        border: { display: false },
        ticks: {
          color: "#4A6285",
          font: { size: 11 },
          callback: (v) => `Rs. ${v}`,
        },
      },
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: {
          color: "#4A6285",
          font: { size: 11 },
        },
      },
    },
  };

  return (
    <div style={{ height: "320px", width: "100%" }}>
      <Line data={data} options={options} />
    </div>
  );
}
