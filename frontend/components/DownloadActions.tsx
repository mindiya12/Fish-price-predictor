"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, Clipboard, CheckCircle2 } from "lucide-react";

type Props = {
  clipboardText: string;
  csvUrl?: string;
  excelUrl?: string;
  csvLabel?: string;
  excelLabel?: string;
  copyLabel?: string;
};

export default function DownloadActions({
  clipboardText,
  csvUrl,
  excelUrl,
  csvLabel = "Download as CSV",
  excelLabel = "Download as Excel",
  copyLabel = "Copy to clipboard",
}: Props) {
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2500);
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(clipboardText);
      showToast("Copied to clipboard!");
    } catch {
      showToast("Copy failed");
    }
  };

  const downloadFile = (url: string, filename: string) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const actions = [
    {
      label: csvLabel,
      icon: <Download size={15} />,
      onClick: () => (csvUrl ? downloadFile(csvUrl, 'forecast_balaya.csv') : showToast("Not available")),
      color: '#00D4FF',
    },
    {
      label: excelLabel,
      icon: <FileSpreadsheet size={15} />,
      onClick: () => (excelUrl ? downloadFile(excelUrl, 'forecast_balaya.xls') : showToast("Not available")),
      color: '#10D9A0',
    },
    {
      label: copyLabel,
      icon: <Clipboard size={15} />,
      onClick: copyToClipboard,
      color: '#00B4A0',
    },
  ];

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
      {actions.map((action) => (
        <button
          key={action.label}
          type="button"
          onClick={action.onClick}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.625rem 1.125rem',
            borderRadius: '0.625rem',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s',
            color: action.color,
            background: `${action.color}0D`,
            border: `1px solid ${action.color}25`,
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.background = `${action.color}1A`;
            (e.currentTarget as HTMLElement).style.borderColor = `${action.color}45`;
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.background = `${action.color}0D`;
            (e.currentTarget as HTMLElement).style.borderColor = `${action.color}25`;
          }}
        >
          {action.icon}
          {action.label}
        </button>
      ))}

      {toast && (
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '0.375rem',
          fontSize: '0.8rem', fontWeight: 600,
          color: '#10D9A0',
          background: 'rgba(16, 217, 160, 0.1)',
          border: '1px solid rgba(16, 217, 160, 0.2)',
          padding: '0.5rem 0.875rem',
          borderRadius: '0.625rem',
        }}>
          <CheckCircle2 size={14} />
          {toast}
        </div>
      )}
    </div>
  );
}
