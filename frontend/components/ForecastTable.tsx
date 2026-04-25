"use client";

import type { ForecastPoint } from "@/types";
import { motion, useReducedMotion } from "framer-motion";
import { easeOut } from "framer-motion";

type Props = {
  rows: ForecastPoint[];
};

export default function ForecastTable({ rows }: Props) {
  const reduceMotion = useReducedMotion();

  const containerVariants = {
    hidden: {},
    show: { transition: { staggerChildren: reduceMotion ? 0 : 0.06 } },
  };

  const rowVariants = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { duration: 0.25, ease: easeOut } },
  };

  return (
    <div className="overflow-x-auto">
      <motion.table
        className="w-full min-w-[520px] table-auto border-separate border-spacing-0 text-sm"
        variants={containerVariants}
        initial={reduceMotion ? false : "hidden"}
        animate={reduceMotion ? false : "show"}
      >
        <thead>
          <tr className="text-left text-brand-neutral bg-brand-light/60">
            <th className="border-b border-brand-light px-3 py-3 font-semibold text-xs uppercase tracking-wide text-brand-primary">Day</th>
            <th className="border-b border-brand-light px-3 py-3 font-semibold text-xs uppercase tracking-wide text-brand-primary">Date</th>
            <th className="border-b border-brand-light px-3 py-3 font-semibold text-xs uppercase tracking-wide text-brand-primary">Predicted price</th>
            <th className="border-b border-brand-light px-3 py-3 font-semibold text-xs uppercase tracking-wide text-brand-primary">Confidence</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <motion.tr
              key={`${row.day}-${row.dateLabel}`}
              variants={rowVariants}
              className="odd:bg-white even:bg-brand-light/40 hover:bg-brand-light transition"
            >
              <td className="border-b border-slate-100 px-3 py-3">{row.day}</td>
              <td className="border-b border-slate-100 px-3 py-3">{row.dateLabel}</td>
              <td className="border-b border-slate-100 px-3 py-3 font-semibold text-brand-primary">
                Rs. {row.prediction}
              </td>
              <td className="border-b border-slate-100 px-3 py-3 text-brand-neutral">
                ± {row.confidence} Rs
              </td>
            </motion.tr>
          ))}
        </tbody>
      </motion.table>
    </div>
  );
}
