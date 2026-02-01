import Link from "next/link";
import Image from "next/image";

import FishSelector from "@/components/FishSelector";
import ForecastTable from "@/components/ForecastTable";
import UpdateBadge from "@/components/UpdateBadge";
import DownloadCsvButton from "@/components/DownloadCsvButton";
import HistoricalChartSection from "@/components/HistoricalChartSection";
import ForecastSummaryCards from "@/components/ForecastSummaryCards";

import { detailedForecast7Days } from "@/lib/dummyDataForecast";

export default function HomePage() {
  const lastUpdatedIso = "2025-12-27T00:05:00+05:30";
  const nextUpdateIso = "2025-12-28T00:05:00+05:30";

  const forecastCsvDownloadUrl = "/api/download/forecast?format=csv";

  return (
    <div className="space-y-6">
      {/* Full-width hero banner */}
      <section className="relative left-1/2 right-1/2 -ml-[50vw] -mr-[50vw] w-screen overflow-hidden">
        <div className="relative h-[260px] sm:h-[320px] md:h-[440px]">
          <Image
            src="/hero2.png"
            alt="Fish market in Sri Lanka"
            fill
            priority
            className="object-cover object-[75%_50%] sm:object-center"
          />

          <div className="absolute inset-0 bg-gradient-to-r from-slate-950/70 via-slate-950/35 to-transparent" />

          <div className="absolute inset-0">
            <div className="mx-auto flex h-full w-full max-w-6xl items-end md:items-center px-4 pb-8 md:pb-0 pt-16 md:pt-0">
              {/* Fade-up once */}
              <div className="max-w-xl opacity-0 translate-y-2 motion-safe:animate-[heroFadeUp_650ms_ease-out_forwards] motion-reduce:opacity-100 motion-reduce:translate-y-0">
                {/* Float forever */}
                <div className="motion-safe:animate-[heroFloat_8s_ease-in-out_infinite] motion-reduce:animate-none">
                  <h1 className="font-[var(--font-poppins)] text-3xl sm:text-4xl md:text-6xl font-semibold tracking-tight text-white">
                    Fish price forecast
                  </h1>

                  <p className="mt-2 text-sm sm:text-base md:text-xl text-white/85">
                    Today’s price + next 7 days for Balaya (Peliyagoda).
                  </p>

                  <div className="mt-4 hidden sm:flex flex-wrap gap-2 text-sm">
                    <span className="rounded-full bg-white/15 px-3 py-1 text-white/90 ring-1 ring-white/20">
                      Today + confidence
                    </span>
                    <span className="rounded-full bg-white/15 px-3 py-1 text-white/90 ring-1 ring-white/20">
                      7-day predictions
                    </span>
                    <span className="rounded-full bg-white/15 px-3 py-1 text-white/90 ring-1 ring-white/20">
                      History + export
                    </span>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-3">
                    <Link
                      href="/forecast"
                      className="rounded-lg bg-brand-primary px-5 py-3 text-sm sm:text-base text-white shadow-sm transition hover:bg-brand-secondary"
                    >
                      View forecast
                    </Link>

                    <Link
                      href="/history"
                      className="rounded-lg bg-white/10 px-5 py-3 text-sm sm:text-base text-white ring-1 ring-white/25 backdrop-blur transition hover:bg-white/15"
                    >
                      View history
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <FishSelector />

      <ForecastSummaryCards rows={detailedForecast7Days} wowPercent={-2.1} />

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="font-[var(--font-poppins)] text-lg">Forecast details</h2>
          <UpdateBadge lastUpdatedIso={lastUpdatedIso} nextUpdateIso={nextUpdateIso} />
        </div>

        <ForecastTable rows={detailedForecast7Days} />
      </section>

      <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <div className="mt-4 rounded-xl bg-brand-background p-6 text-sm text-brand-neutral">
          <HistoricalChartSection fishName="Balaya" location="Peliyagoda" />
        </div>
      </section>

      <section className="flex flex-wrap gap-3">
        <Link
          href="/forecast"
          className="rounded-lg bg-brand-primary px-4 py-2 text-sm text-white shadow-sm transition hover:bg-brand-secondary"
        >
          View detailed forecast
        </Link>

        <DownloadCsvButton downloadUrl={forecastCsvDownloadUrl} />
      </section>

      <section id="about" className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        <h2 className="font-[var(--font-poppins)] text-lg">About</h2>
        <p className="mt-2 text-sm text-brand-neutral">
          FishPrice.LK predicts Balaya prices using AI. Currently serving Peliyagoda market.
        </p>
      </section>

      <section id="contact" className="hidden" />
      <section id="data-sources" className="hidden" />
      <section id="disclaimer" className="hidden" />
    </div>
  );
}
