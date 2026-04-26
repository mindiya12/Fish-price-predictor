'use client';

import { useState } from 'react';
import { Database, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function PipelinePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const triggerScrape = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/admin/scrape-daily`, {
        method: 'POST',
      });
      const data = await res.json();
      
      if (res.ok) {
        setResult(data);
      } else {
        setError(data.detail || 'An error occurred triggering the pipeline.');
      }
    } catch (err) {
      setError('Network error: Could not reach the backend API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Pipeline</h1>
        <p className="text-zinc-400 mt-2">Manage automated scrapers and trigger manual data pulls.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
              <Database size={20} />
            </div>
            <h2 className="text-lg font-bold">Manual Pipeline Trigger</h2>
          </div>
          
          <p className="text-zinc-400 mb-6 text-sm leading-relaxed">
            The automated pipeline runs daily at 5:00 AM via GitHub Actions. If today&apos;s CBSL report was published late, or you noticed missing data, you can force a manual trigger here.
          </p>

          <button
            onClick={triggerScrape}
            disabled={loading}
            className="flex items-center justify-center gap-2 w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Running Full Pipeline...' : 'Run Daily Pipeline Now'}
          </button>

          {error && (
            <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
              <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={18} />
              <div className="text-red-400 text-sm">{error}</div>
            </div>
          )}

          {result && (
            <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-emerald-400 font-medium">
                <CheckCircle2 size={18} />
                Pipeline Execution Complete
              </div>
              <div className="text-sm text-zinc-300 bg-black/20 p-3 rounded-lg font-mono">
                <div>Status: {result.status}</div>
                <div>Message: {result.message}</div>
                <div>Date Processed: {result.date}</div>
                {result.price !== null && <div>Price Scraped: Rs. {result.price}</div>}
              </div>
            </div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-lg font-bold mb-6">Pipeline Health</h2>
          <div className="space-y-4">
            <HealthItem name="PostgreSQL Database (Supabase)" status="operational" />
            <HealthItem name="CBSL Daily PDF Scraper" status={result?.status === 'success' || !result ? 'operational' : 'error'} />
            <HealthItem name="Open-Meteo Weather API" status={result?.weather_fetched === false ? 'warning' : 'operational'} />
            <HealthItem name="XGBoost Inference Engine" status="operational" />
          </div>
        </div>
      </div>
    </div>
  );
}

function HealthItem({ name, status }: { name: string, status: 'operational' | 'warning' | 'error' }) {
  const colors = {
    operational: 'bg-emerald-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500'
  };
  
  return (
    <div className="flex items-center justify-between p-4 bg-zinc-950 border border-zinc-800 rounded-xl">
      <span className="font-medium text-sm text-zinc-300">{name}</span>
      <div className="flex items-center gap-2">
        <div className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">
          {status}
        </div>
        <div className={`w-2 h-2 rounded-full ${colors[status]}`}></div>
      </div>
    </div>
  );
}
