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
      className="rounded-lg border border-brand-neutral/20 bg-white px-4 py-2 text-sm text-brand-neutral shadow-subtle transition hover:bg-brand-light hover:border-brand-accent/50"
    >
      {label}
    </button>
  );
}
