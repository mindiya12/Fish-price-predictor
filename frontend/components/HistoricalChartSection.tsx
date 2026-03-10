"use client";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import HistoryChart from "@/components/HistoryChart";
import { getHistory } from "@/lib/api";

export interface HistoryPoint {
  dateIso: string;
  dateLabel: string;
  price: number;
}

export default function HistoricalChartSection({
  fishName = "Balaya",
  location = "Peliyagoda",
}: {
  fishName?: string;
  location?: string;
}) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch the last 30 days dynamically
        const toDate = new Date();
        const fromDate = new Date();
        fromDate.setDate(toDate.getDate() - 30);

        const toStr = toDate.toISOString().slice(0, 10);
        const fromStr = fromDate.toISOString().slice(0, 10);

        const rawData = await getHistory(fromStr, toStr, fishName.toLowerCase(), location.toLowerCase());

        if (rawData && rawData.dates) {
          const transformed = rawData.dates.map((dateIso: string, i: number) => ({
            dateIso,
            dateLabel: new Date(dateIso).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            price: Math.round(rawData.prices[i]),
          }));
          setRows(transformed);
        }
      } catch (error) {
        console.error("Failed to load historical chart", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [fishName, location]);

  const avg = rows.length > 0 ? Math.round(rows.reduce((s, p) => s + p.price, 0) / rows.length) : 0;
  const min = rows.length > 0 ? Math.min(...rows.map((p) => p.price)) : 0;
  const max = rows.length > 0 ? Math.max(...rows.map((p) => p.price)) : 0;

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3"
      >
        <div className="text-left">
          <h2 className="font-[var(--font-poppins)] text-lg">
            {fishName} history — {location}
          </h2>
          <p className="text-sm text-brand-neutral">
            {loading ? "Loading data..." : rows.length === 0 ? "No data found." : `Average Rs. ${avg} • Range Rs. ${min}–${max}`}
          </p>
        </div>

        <ChevronDown className={`h-5 w-5 transition ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence initial={false}>
        {open && !loading && rows.length > 0 ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 overflow-hidden"
          >
            <div className="text-xs text-brand-neutral mb-2">
              Tip: Hover or tap the line to see the exact price for a day.
            </div>
            <HistoryChart rows={rows} />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}
