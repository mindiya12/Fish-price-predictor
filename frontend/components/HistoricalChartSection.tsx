"use client";

import { useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import HistoryChart from "@/components/HistoryChart";
import type { HistoryPoint } from "@/lib/dummyHistory";

export default function HistoricalChartSection({
  fishName = "Balaya",
  location = "Negombo",
  data,
}: {
  fishName?: string;
  location?: string;
  data?: HistoryPoint[];
}) {
  const [open, setOpen] = useState(false);

  const fallback: HistoryPoint[] = useMemo(() => {
    const out: HistoryPoint[] = [];
    const start = new Date();
    start.setDate(start.getDate() - 29);

    let price = 690;
    for (let i = 0; i < 30; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      price = Math.round(price + (i % 6 === 0 ? -8 : 6) + Math.sin(i / 4) * 3);

      out.push({
        dateIso: d.toISOString().slice(0, 10),
        dateLabel: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        price,
      });
    }
    return out;
  }, []);

  const rows = data?.length ? data : fallback;

  const avg = Math.round(rows.reduce((s, p) => s + p.price, 0) / rows.length);
  const min = Math.min(...rows.map((p) => p.price));
  const max = Math.max(...rows.map((p) => p.price));

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
            Average Rs. {avg} • Range Rs. {min}–{max}
          </p>
        </div>

        <ChevronDown className={`h-5 w-5 transition ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence initial={false}>
        {open ? (
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
