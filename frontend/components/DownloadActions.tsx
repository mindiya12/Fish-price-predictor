"use client";

import { useState } from "react";

type Props = {
  clipboardText: string;
  csvUrl?: string;
  excelUrl?: string;
  csvLabel?: string;
  excelLabel?: string;
  copyLabel?: string;
};

const btn =
  "rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50";

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

  const backendNotReady = () => showToast("Backend not connected");

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(clipboardText);
      showToast("Copied!");
    } catch {
      showToast("Copy failed");
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        className={btn}
        onClick={() => (csvUrl ? (window.location.href = csvUrl) : backendNotReady())}
      >
        {csvLabel}
      </button>

      <button
        type="button"
        className={btn}
        onClick={() => (excelUrl ? (window.location.href = excelUrl) : backendNotReady())}
      >
        {excelLabel}
      </button>

      <button type="button" className={btn} onClick={copyToClipboard}>
        {copyLabel}
      </button>

      {toast ? (
        <div className="text-sm text-slate-700 rounded-lg bg-brand-light px-3 py-2 ring-1 ring-black/5">
          {toast}
        </div>
      ) : null}
    </div>
  );
}
