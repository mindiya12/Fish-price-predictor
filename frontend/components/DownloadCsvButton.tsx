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
      className="btn-ghost"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0.625rem 1.5rem',
        borderRadius: '0.625rem',
        fontSize: '0.95rem',
        fontWeight: 600,
        textDecoration: 'none'
      }}
    >
      {label}
    </button>
  );
}
