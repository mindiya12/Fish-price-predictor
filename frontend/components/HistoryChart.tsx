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
        borderColor: "#64748B",
        backgroundColor: "rgba(219, 234, 254, 0.25)",
        tension: 0.35,
        fill: true,
        pointRadius: 0,
      },
    ],
  };

  const options: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: "index" },
    plugins: {
      legend: { display: false },
      tooltip: { intersect: false, mode: "index" },
    },
    scales: {
      y: {
        ticks: {
          callback: (v) => `Rs. ${v}`,
        },
      },
      x: {
        ticks: { maxTicksLimit: 10 },
        grid: { display: false },
      },
    },
  };

  return (
    <div className="h-[360px] w-full">
      <Line data={data} options={options} />
    </div>
  );
}
