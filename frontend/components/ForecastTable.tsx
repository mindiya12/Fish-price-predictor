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
          <tr className="text-left text-slate-600">
            <th className="border-b border-slate-200 px-3 py-2">Day</th>
            <th className="border-b border-slate-200 px-3 py-2">Date</th>
            <th className="border-b border-slate-200 px-3 py-2">Predicted price</th>
            <th className="border-b border-slate-200 px-3 py-2">Confidence</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <motion.tr
              key={`${row.day}-${row.dateLabel}`}
              variants={rowVariants}
              className="odd:bg-white even:bg-brand-light/40 hover:bg-brand-light transition"
            >
              <td className="border-b border-slate-100 px-3 py-2">{row.day}</td>
              <td className="border-b border-slate-100 px-3 py-2">{row.dateLabel}</td>
              <td className="border-b border-slate-100 px-3 py-2 font-medium text-slate-900">
                Rs. {row.prediction}
              </td>
              <td className="border-b border-slate-100 px-3 py-2 text-slate-700">
                ± {row.confidence} Rs
              </td>
            </motion.tr>
          ))}
        </tbody>
      </motion.table>
    </div>
  );
}
