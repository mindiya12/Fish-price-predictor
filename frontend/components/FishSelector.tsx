"use client";

import { useId, useMemo, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { FISH_TYPES } from "@/lib/constants";

type FishKey = (typeof FISH_TYPES)[number]["key"];
type FishType = (typeof FISH_TYPES)[number];

type Props = {
  value?: FishKey;
  onChange?: (key: FishKey) => void;
  fishTypes?: readonly FishType[];
};

export default function FishSelector({ value, onChange, fishTypes }: Props) {
  const reduceMotion = useReducedMotion();
  const tooltipIdPrefix = useId();

  const items = useMemo(() => fishTypes ?? FISH_TYPES, [fishTypes]);

  const [internal, setInternal] = useState<FishKey>("balaya");
  const activeKey = value ?? internal;

  const setActiveKey = (k: FishKey) => {
    onChange?.(k);
    if (value == null) setInternal(k);
  };

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-black/5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-[var(--font-poppins)] text-lg">Fish type</h2>
        <p className="text-xs text-brand-neutral">More species coming soon</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {items.map((fish) => {
          const isActive = fish.key === activeKey;
          const isDisabled = !fish.active;
          const tooltipId = `${tooltipIdPrefix}-${fish.key}-tip`;

          return (
            <motion.button
              key={fish.key}
              type="button"
              disabled={isDisabled}
              onClick={() => setActiveKey(fish.key)}
              whileTap={reduceMotion || isDisabled ? undefined : { scale: 0.98 }}
              aria-describedby={isDisabled ? tooltipId : undefined}
              className={[
                "group relative rounded-full px-4 py-2 text-sm transition",
                isActive
                  ? "bg-brand-primary text-white shadow-sm"
                  : "bg-white text-slate-700 ring-1 ring-black/10 hover:bg-brand-light",
                isDisabled ? "cursor-not-allowed opacity-60 hover:bg-white" : "",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2",
              ].join(" ")}
            >
              <span className="flex items-center gap-2">
                {fish.label}
                {isDisabled ? (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-500">
                    Coming Soon
                  </span>
                ) : null}
              </span>

              {isDisabled ? (
                <span
                  id={tooltipId}
                  role="tooltip"
                  className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 w-max -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-1 text-[11px] text-white opacity-0 shadow-sm ring-1 ring-black/10 transition group-hover:opacity-100 group-focus-visible:opacity-100"
                >
                  Available soon
                </span>
              ) : null}
            </motion.button>
          );
        })}
      </div>
    </section>
  );
}
