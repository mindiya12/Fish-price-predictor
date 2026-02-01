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

type Props = {
  rows: ForecastPoint[];
};

export default function ForecastPredictionChart({ rows }: Props) {
  const labels = rows.map((d) => d.dateLabel);
  const prediction = rows.map((d) => d.prediction);

  const hasBand = rows.every((d) => typeof d.lower === "number" && typeof d.upper === "number");
  const lower = hasBand ? rows.map((d) => d.lower as number) : undefined;
  const upper = hasBand ? rows.map((d) => d.upper as number) : undefined;

  const datasets: any[] = [];

  // Confidence band (fill between upper & lower)
  if (hasBand && lower && upper) {
    datasets.push(
      {
        label: "Upper",
        data: upper,
        borderColor: "transparent",
        pointRadius: 0,
      },
      {
        label: "Lower",
        data: lower,
        borderColor: "transparent",
        pointRadius: 0,
        fill: "-1",
        backgroundColor: "rgba(219, 234, 254, 0.35)",
      }
    );
  }

  // Main prediction line
  datasets.push({
    label: "Prediction",
    data: prediction,
    borderColor: "#0A7AFF",
    backgroundColor: "rgba(10, 122, 255, 0.10)",
    tension: 0.35,
    pointRadius: 2,
    pointHoverRadius: 4,
    fill: false,
  });

  const data = { labels, datasets };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      tooltip: { intersect: false, mode: "index" },
      legend: {
        labels: {
          filter: (item) => item.text === "Prediction",
        },
      },
    },
    scales: {
      y: {
        ticks: { callback: (v) => `Rs. ${v}` },
      },
    },
  };

  return (
    <div className="h-[320px] w-full">
      <Line data={data} options={options} />
    </div>
  );
}
