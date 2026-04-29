'use client';

import { useEffect, useState } from 'react';
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

export default function PerformancePage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedHorizon, setSelectedHorizon] = useState(1);

  useEffect(() => {
    const fetchPerf = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
        const res = await fetch(`${apiUrl}/api/admin/performance?days=30`).then(r => r.json());
        if (res.status === 'success') {
          setData(res.data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPerf();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>;
  }

  // Filter by selected horizon
  const horizonData = data.filter(d => d.horizon === selectedHorizon);

  const chartData = {
    labels: horizonData.map(d => d.date),
    datasets: [
      {
        label: 'Actual Price (Rs)',
        data: horizonData.map(d => d.actual),
        borderColor: '#3b82f6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
      },
      {
        label: `Predicted Price (Day ${selectedHorizon})`,
        data: horizonData.map(d => d.predicted),
        borderColor: '#f59e0b', // amber-500
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

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl flex-1 flex flex-col min-h-[500px]">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
            <ArrowRightLeft size={20} />
          </div>
          <h2 className="text-lg font-bold">Actual vs Predicted (Last 30 Days)</h2>
        </div>
        
        <div className="flex-1 w-full relative">
          {horizonData.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-zinc-500 flex-col gap-2">
              <ArrowRightLeft size={32} className="opacity-50" />
              <p>Not enough historical data for this horizon yet.</p>
            </div>
          ) : (
            <Line data={chartData} options={chartOptions} />
          )}
        </div>
      </div>
    </div>
  );
}
