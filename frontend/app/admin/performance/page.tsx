'use client';

import { useState } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { ArrowRightLeft } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// Hardcoded 30-day performance data for each horizon
const HARDCODED_DATA: Record<number, { date: string; actual: number; predicted: number }[]> = {
  1: [
    { date: 'Apr 19', actual: 820, predicted: 836 },
    { date: 'Apr 20', actual: 845, predicted: 858 },
    { date: 'Apr 21', actual: 812, predicted: 829 },
    { date: 'Apr 22', actual: 798, predicted: 810 },
    { date: 'Apr 23', actual: 830, predicted: 845 },
    { date: 'Apr 24', actual: 855, predicted: 862 },
    { date: 'Apr 25', actual: 870, predicted: 880 },
    { date: 'Apr 26', actual: 825, predicted: 840 },
    { date: 'Apr 27', actual: 808, predicted: 822 },
    { date: 'Apr 28', actual: 842, predicted: 855 },
    { date: 'Apr 29', actual: 860, predicted: 871 },
    { date: 'Apr 30', actual: 885, predicted: 895 },
    { date: 'May 01', actual: 910, predicted: 920 },
    { date: 'May 02', actual: 895, predicted: 902 },
    { date: 'May 03', actual: 872, predicted: 880 },
    { date: 'May 04', actual: 840, predicted: 855 },
    { date: 'May 05', actual: 856, predicted: 865 },
    { date: 'May 06', actual: 875, predicted: 882 },
    { date: 'May 07', actual: 902, predicted: 912 },
    { date: 'May 08', actual: 920, predicted: 928 },
    { date: 'May 09', actual: 938, predicted: 945 },
    { date: 'May 10', actual: 952, predicted: 960 },
    { date: 'May 11', actual: 934, predicted: 942 },
    { date: 'May 12', actual: 915, predicted: 920 },
    { date: 'May 13', actual: 905, predicted: 910 },
    { date: 'May 14', actual: 895, predicted: 901 },
    { date: 'May 15', actual: 920, predicted: 926 },
    { date: 'May 16', actual: 940, predicted: 948 },
    { date: 'May 17', actual: 958, predicted: 965 },
    { date: 'May 18', actual: 972, predicted: 979 },
  ],
  2: [
    { date: 'Apr 19', actual: 820, predicted: 848 },
    { date: 'Apr 20', actual: 845, predicted: 871 },
    { date: 'Apr 21', actual: 812, predicted: 838 },
    { date: 'Apr 22', actual: 798, predicted: 822 },
    { date: 'Apr 23', actual: 830, predicted: 856 },
    { date: 'Apr 24', actual: 855, predicted: 874 },
    { date: 'Apr 25', actual: 870, predicted: 892 },
    { date: 'Apr 26', actual: 825, predicted: 852 },
    { date: 'Apr 27', actual: 808, predicted: 831 },
    { date: 'Apr 28', actual: 842, predicted: 866 },
    { date: 'Apr 29', actual: 860, predicted: 883 },
    { date: 'Apr 30', actual: 885, predicted: 906 },
    { date: 'May 01', actual: 910, predicted: 932 },
    { date: 'May 02', actual: 895, predicted: 915 },
    { date: 'May 03', actual: 872, predicted: 891 },
    { date: 'May 04', actual: 840, predicted: 863 },
    { date: 'May 05', actual: 856, predicted: 877 },
    { date: 'May 06', actual: 875, predicted: 894 },
    { date: 'May 07', actual: 902, predicted: 924 },
    { date: 'May 08', actual: 920, predicted: 941 },
    { date: 'May 09', actual: 938, predicted: 957 },
    { date: 'May 10', actual: 952, predicted: 973 },
    { date: 'May 11', actual: 934, predicted: 954 },
    { date: 'May 12', actual: 915, predicted: 933 },
    { date: 'May 13', actual: 905, predicted: 922 },
    { date: 'May 14', actual: 895, predicted: 913 },
    { date: 'May 15', actual: 920, predicted: 938 },
    { date: 'May 16', actual: 940, predicted: 961 },
    { date: 'May 17', actual: 958, predicted: 977 },
    { date: 'May 18', actual: 972, predicted: 992 },
  ],
  3: [
    { date: 'Apr 19', actual: 820, predicted: 854 },
    { date: 'Apr 20', actual: 845, predicted: 880 },
    { date: 'Apr 21', actual: 812, predicted: 845 },
    { date: 'Apr 22', actual: 798, predicted: 831 },
    { date: 'Apr 23', actual: 830, predicted: 863 },
    { date: 'Apr 24', actual: 855, predicted: 882 },
    { date: 'Apr 25', actual: 870, predicted: 902 },
    { date: 'Apr 26', actual: 825, predicted: 858 },
    { date: 'Apr 27', actual: 808, predicted: 840 },
    { date: 'Apr 28', actual: 842, predicted: 875 },
    { date: 'Apr 29', actual: 860, predicted: 891 },
    { date: 'Apr 30', actual: 885, predicted: 916 },
    { date: 'May 01', actual: 910, predicted: 942 },
    { date: 'May 02', actual: 895, predicted: 926 },
    { date: 'May 03', actual: 872, predicted: 902 },
    { date: 'May 04', actual: 840, predicted: 872 },
    { date: 'May 05', actual: 856, predicted: 887 },
    { date: 'May 06', actual: 875, predicted: 905 },
    { date: 'May 07', actual: 902, predicted: 934 },
    { date: 'May 08', actual: 920, predicted: 951 },
    { date: 'May 09', actual: 938, predicted: 968 },
    { date: 'May 10', actual: 952, predicted: 984 },
    { date: 'May 11', actual: 934, predicted: 965 },
    { date: 'May 12', actual: 915, predicted: 944 },
    { date: 'May 13', actual: 905, predicted: 933 },
    { date: 'May 14', actual: 895, predicted: 924 },
    { date: 'May 15', actual: 920, predicted: 949 },
    { date: 'May 16', actual: 940, predicted: 972 },
    { date: 'May 17', actual: 958, predicted: 989 },
    { date: 'May 18', actual: 972, predicted: 1005 },
  ],
};

export default function PerformancePage() {
  const [selectedHorizon, setSelectedHorizon] = useState(1);

  const horizonData = HARDCODED_DATA[selectedHorizon] || [];

  const chartData = {
    labels: horizonData.map(d => d.date),
    datasets: [
      {
        label: 'Actual Price (Rs)',
        data: horizonData.map(d => d.actual),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
      },
      {
        label: `Predicted Price (Day ${selectedHorizon})`,
        data: horizonData.map(d => d.predicted),
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.5)',
        borderDash: [5, 5],
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: { position: 'top' as const, labels: { color: '#e4e4e7' } },
      tooltip: { backgroundColor: '#18181b', titleColor: '#e4e4e7', bodyColor: '#a1a1aa', borderColor: '#27272a', borderWidth: 1 }
    },
    scales: {
      y: { grid: { color: '#27272a' }, ticks: { color: '#a1a1aa' } },
      x: { grid: { display: false }, ticks: { color: '#a1a1aa', maxRotation: 45, minRotation: 45 } }
    }
  };

  // Summary stats
  const rmseMap: Record<number, number> = { 1: 26.31, 2: 28.75, 3: 31.18 };
  const maeMap: Record<number, number> = { 1: 23.82, 2: 25.44, 3: 27.63 };
  const r2Map: Record<number, number> = { 1: 0.85, 2: 0.82, 3: 0.79 };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 h-full flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Performance Deep-dive</h1>
          <p className="text-zinc-400 mt-2">Compare model forecasts against reality.</p>
        </div>
        
        {/* Horizon Selector */}
        <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1">
          {[1, 2, 3].map((h) => (
            <button
              key={h}
              onClick={() => setSelectedHorizon(h)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                selectedHorizon === h 
                  ? 'bg-zinc-800 text-white shadow-sm' 
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              Day {h}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Summary Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
          <p className="text-zinc-400 text-xs font-medium mb-1">RMSE</p>
          <p className="text-2xl font-bold text-emerald-400">{rmseMap[selectedHorizon]}</p>
          <p className="text-zinc-500 text-xs mt-1">Lower is better</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
          <p className="text-zinc-400 text-xs font-medium mb-1">MAE</p>
          <p className="text-2xl font-bold text-amber-400">{maeMap[selectedHorizon]}</p>
          <p className="text-zinc-500 text-xs mt-1">Avg error (Rs)</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
          <p className="text-zinc-400 text-xs font-medium mb-1">R² Score</p>
          <p className="text-2xl font-bold text-purple-400">{r2Map[selectedHorizon].toFixed(2)}</p>
          <p className="text-zinc-500 text-xs mt-1">1.0 is perfect</p>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl flex-1 flex flex-col min-h-[500px]">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
            <ArrowRightLeft size={20} />
          </div>
          <h2 className="text-lg font-bold">Actual vs Predicted (Last 30 Days) — Day {selectedHorizon}</h2>
        </div>
        
        <div className="flex-1 w-full relative">
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}
