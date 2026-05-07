'use client';

import { useState } from 'react';
import { FileText, Download, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api';

export default function ProcurementReportButton() {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/reports/procurement?fish=balaya&location=peliyagoda`);
      if (!response.ok) throw new Error('Report generation failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `procurement_report_balaya_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
      alert('Failed to download report. Please check if forecast data is available.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className="glass glass-hover"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        padding: '1rem 1.5rem',
        borderRadius: '0.875rem',
        color: '#EDF4FF',
        border: '1px solid rgba(100, 180, 255, 0.15)',
        cursor: 'pointer',
        fontSize: '0.9rem',
        fontWeight: 600,
        transition: 'all 0.2s',
        width: '100%',
        background: 'rgba(255, 255, 255, 0.03)',
      }}
    >
      <div style={{
        width: '32px', height: '32px',
        borderRadius: '8px',
        background: 'rgba(0, 212, 255, 0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#00D4FF'
      }}>
        {loading ? <Loader2 size={18} className="animate-spin" /> : <FileText size={18} />}
      </div>
      <div style={{ textAlign: 'left', flex: 1 }}>
        <div style={{ fontSize: '0.875rem' }}>Smart Procurement Report</div>
        <div style={{ fontSize: '0.7rem', color: '#4A6285', fontWeight: 500 }}>Download weekly PDF digest</div>
      </div>
      <Download size={16} color="#4A6285" />
    </button>
  );
}
