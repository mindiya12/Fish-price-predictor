"use client";

type Props = {
  label?: string;
  downloadUrl: string;
};

export default function DownloadCsvButton({
  label = "Download 7-day data (CSV)",
  downloadUrl,
}: Props) {
  return (
    <button
      type="button"
      onClick={() => {
        window.location.href = downloadUrl;
      }}
      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50"
    >
      {label}
    </button>
  );
}
