'use client';

import { useEffect, useState } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Users, Target, Activity, Zap } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>({ chart: [], total_views: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const [metricsRes, analyticsRes] = await Promise.all([
          fetch(`${apiUrl}/api/admin/metrics`).then(r => r.json()),
          fetch(`${apiUrl}/api/admin/analytics`).then(r => r.json())
        ]);
        
        if (metricsRes.status === 'success') setMetrics(metricsRes.data);
        if (analyticsRes.status === 'success') setAnalytics(analyticsRes.data);
      } catch (err) {
        console.error("Failed to fetch admin data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div></div>;
  }

  // Use Horizon 1 metrics for the KPI cards
  const h1Metrics = metrics.find(m => m.horizon === 1) || { rmse: 0, mae: 0, mape: 0, r2_score: 0 };

  const chartData = {
    labels: analytics.chart.map((d: any) => d.date),
    datasets: [
      {
        label: 'Page Views',
        data: analytics.chart.map((d: any) => d.views),
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderRadius: 4,
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: { grid: { color: '#27272a' }, ticks: { color: '#a1a1aa' } },
      x: { grid: { display: false }, ticks: { color: '#a1a1aa' } }
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard Overview</h1>
        <p className="text-zinc-400 mt-2">Monitor model health and website traffic.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Total Page Views" 
          value={analytics.total_views.toLocaleString()} 
          icon={<Users size={20} className="text-blue-400" />} 
          trend="+12% this week"
        />
        <MetricCard 
          title="1-Day RMSE" 
          value={h1Metrics.rmse.toFixed(2)} 
          icon={<Target size={20} className="text-emerald-400" />} 
          trend="Lower is better"
        />
        <MetricCard 
          title="1-Day MAE" 
          value={h1Metrics.mae.toFixed(2)} 
          icon={<Activity size={20} className="text-amber-400" />} 
          trend={`Avg Error Rs. ${h1Metrics.mae.toFixed(0)}`}
        />
        <MetricCard 
          title="R² Score" 
          value={h1Metrics.r2_score.toFixed(2)} 
          icon={<Zap size={20} className="text-purple-400" />} 
          trend="1.0 is perfect"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Traffic Chart */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-bold mb-6">Traffic Over Time (7 Days)</h2>
          <div className="h-64">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* Multi-Horizon Metrics Table */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl flex flex-col">
          <h2 className="text-lg font-bold mb-6">Active Model Metrics</h2>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-400 text-sm">
                  <th className="pb-3 font-medium">Horizon</th>
                  <th className="pb-3 font-medium">RMSE</th>
                  <th className="pb-3 font-medium">MAE</th>
                  <th className="pb-3 font-medium">R² Score</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {metrics.map((m) => (
                  <tr key={m.horizon} className="border-b border-zinc-800/50 hover:bg-zinc-800/20 transition-colors">
                    <td className="py-4 font-medium flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                      Day {m.horizon}
                    </td>
                    <td className="py-4">{m.rmse.toFixed(2)}</td>
                    <td className="py-4">{m.mae.toFixed(2)}</td>
                    <td className="py-4">
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${m.r2_score > 0.5 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                        {m.r2_score.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, trend }: { title: string, value: string | number, icon: React.ReactNode, trend: string }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow group">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-zinc-400 font-medium">{title}</h3>
        <div className="p-2 bg-zinc-800 rounded-lg group-hover:scale-110 transition-transform">
          {icon}
        </div>
      </div>
      <div className="text-3xl font-bold tracking-tight mb-2">{value}</div>
      <div className="text-xs text-zinc-500 font-medium">{trend}</div>
    </div>
  );
}
