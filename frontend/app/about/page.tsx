import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-poppins)] text-3xl font-semibold tracking-tight">
            About FishPrice.LK
          </h1>
          <p className="mt-1 text-brand-neutral">
            FishPrice.LK predicts fish prices using historical market data and machine learning.
          </p>
        </div>

        <Link
          href="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          ← Back to Home
        </Link>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">What this site shows</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-700">
          <li>7-day forecast for selected fish (MVP).</li>
          <li>Detailed forecast view with prediction chart + table.</li>
          <li>Historical trend chart with selectable date ranges.</li>
        </ul>

        <p className="mt-4 text-sm text-brand-neutral">
          Note: This is an MVP and more species/markets will be added over time.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Data sources</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-slate-700">
          <li>Manual CSV uploads of daily fish market prices (MVP).</li>
          <li>Future: weather and other external signals (Phase 2).</li>
        </ul>

        {/* TODO BACKEND INTEGRATION:
            Later you can fetch and display:
            - last updated timestamp (GET /api/health or /api/forecast/latest)
            - current production model version (GET /api/metrics)
        */}
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Disclaimer</h2>
        <p className="mt-3 text-slate-700">
          Forecasts are estimates and can be wrong. This website is for informational purposes only
          and should not be used as the sole basis for business or trading decisions.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Contact</h2>
        <p className="mt-3 text-slate-700">
          Email: <span className="font-medium">your-email@example.com</span>
        </p>

        {/* TODO:
            Replace with your real contact email / project supervisor email if needed.
        */}
      </section>
    </div>
  );
}
