"use client";

import type { HistoryPoint } from "@/lib/dummyHistory";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  Legend,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler, Legend);

type Props = {
  rows: HistoryPoint[];
  label?: string;
};

export default function HistoryChart({ rows, label = "Actual price" }: Props) {
  const labels = rows.map((r) => r.dateLabel);
  const values = rows.map((r) => r.price);

  const data = {
    labels,
    datasets: [
      {
        label,
        data: values,
        borderColor: "#00D4FF",
        backgroundColor: (context: any) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 300);
          gradient.addColorStop(0, "rgba(0, 212, 255, 0.25)");
          gradient.addColorStop(0.6, "rgba(0, 212, 255, 0.05)");
          gradient.addColorStop(1, "rgba(0, 212, 255, 0)");
          return gradient;
        },
        tension: 0.4,
        fill: true,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#00D4FF",
        pointHoverBorderColor: "#ffffff",
        pointHoverBorderWidth: 2,
        borderWidth: 2,
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      legend: { display: false },
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
          label: (ctx) => `  Rs. ${ctx.parsed.y.toLocaleString()}`,
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
          maxTicksLimit: 8,
          color: "#4A6285",
          font: { size: 11 },
        },
      },
    },
  };

  return (
    <div style={{ height: "300px", width: "100%" }}>
      <Line data={data} options={options} />
    </div>
  );
}
