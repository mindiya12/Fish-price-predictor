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
    <section className="glass" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', gap: '1rem', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '0.875rem', fontWeight: 700, margin: 0 }}>Fish Type</h2>
        <p style={{ fontSize: '0.7rem', color: '#4A6285', margin: 0, fontWeight: 500 }}>More species coming soon</p>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
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
              whileTap={reduceMotion || isDisabled ? undefined : { scale: 0.97 }}
              aria-describedby={isDisabled ? tooltipId : undefined}
              style={{
                position: 'relative',
                padding: '0.4rem 1rem',
                borderRadius: '999px',
                fontSize: '0.825rem',
                fontWeight: 600,
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                border: isActive ? 'none' : '1px solid rgba(100, 180, 255, 0.12)',
                background: isActive
                  ? 'linear-gradient(135deg, #00B4A0, #00D4FF)'
                  : 'rgba(100, 180, 255, 0.05)',
                color: isActive ? '#070B14' : '#7A9CC9',
                boxShadow: isActive ? '0 0 16px rgba(0, 212, 255, 0.3)' : 'none',
                opacity: isDisabled ? 0.5 : 1,
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {fish.label}
                {isDisabled && (
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                    textTransform: 'uppercase',
                    padding: '0.1rem 0.45rem',
                    borderRadius: '999px',
                    background: 'rgba(100, 180, 255, 0.08)',
                    color: '#4A6285',
                  }}>
                    Soon
                  </span>
                )}
              </span>
            </motion.button>
          );
        })}
      </div>
    </section>
  );
}
