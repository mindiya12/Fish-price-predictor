"use client";

import type { ForecastPoint } from "@/types";
import { motion, useReducedMotion } from "framer-motion";
import { Calendar, TrendingUp, TrendingDown } from "lucide-react";

type Props = { rows: ForecastPoint[] };

export default function ForecastTable({ rows }: Props) {
  const reduceMotion = useReducedMotion();

  const containerVariants = {
    hidden: {},
    show: { transition: { staggerChildren: reduceMotion ? 0 : 0.07 } },
  };
  const rowVariants = {
    hidden: { opacity: 0, x: -12 },
    show: { opacity: 1, x: 0, transition: { duration: 0.3 } },
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <motion.table
        style={{ width: '100%', minWidth: '520px', borderCollapse: 'collapse', fontSize: '0.875rem' }}
        variants={containerVariants}
        initial={reduceMotion ? false : "hidden"}
        animate={reduceMotion ? false : "show"}
      >
        <thead>
          <tr>
            {['Day', 'Date', 'Predicted Price', 'Confidence Band'].map(col => (
              <th key={col} style={{
                padding: '0.875rem 1rem',
                textAlign: 'left',
                fontSize: '0.7rem',
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: '#4A6285',
                borderBottom: '1px solid rgba(100, 180, 255, 0.08)',
              }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const isFirst = idx === 0;
            const prevPrice = idx > 0 ? rows[idx - 1].prediction : row.prediction;
            const change = row.prediction - prevPrice;
            const isUp = change > 0;
            const isDown = change < 0;

            return (
              <motion.tr
                key={`${row.day}-${row.dateLabel}`}
                variants={rowVariants}
                style={{
                  background: isFirst ? 'rgba(0, 212, 255, 0.04)' : 'transparent',
                  borderBottom: '1px solid rgba(100, 180, 255, 0.06)',
                  transition: 'background 0.2s',
                  cursor: 'default',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'rgba(100, 180, 255, 0.04)')}
                onMouseLeave={e => (e.currentTarget.style.background = isFirst ? 'rgba(0, 212, 255, 0.04)' : 'transparent')}
              >
                {/* Day */}
                <td style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{
                      width: '28px', height: '28px',
                      borderRadius: '8px',
                      background: isFirst ? 'rgba(0, 212, 255, 0.15)' : 'rgba(100, 180, 255, 0.06)',
                      border: `1px solid ${isFirst ? 'rgba(0, 212, 255, 0.3)' : 'rgba(100, 180, 255, 0.1)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: isFirst ? '#00D4FF' : '#7A9CC9',
                    }}>
                      {row.day}
                    </div>
                    {isFirst && (
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: '#00D4FF', letterSpacing: '0.05em', textTransform: 'uppercase', background: 'rgba(0, 212, 255, 0.1)', padding: '0.15rem 0.5rem', borderRadius: '999px', border: '1px solid rgba(0, 212, 255, 0.2)' }}>
                        Next
                      </span>
                    )}
                  </div>
                </td>

                {/* Date */}
                <td style={{ padding: '1rem', color: '#7A9CC9', fontWeight: 500 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <Calendar size={13} color="#4A6285" />
                    {row.dateLabel}
                  </div>
                </td>

                {/* Price */}
                <td style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                    <span style={{
                      fontFamily: "'Plus Jakarta Sans', sans-serif",
                      fontWeight: 800,
                      fontSize: '1.125rem',
                      color: isFirst ? '#00D4FF' : '#EDF4FF',
                    }}>
                      Rs. {row.prediction.toLocaleString()}
                    </span>
                    {idx > 0 && (isUp || isDown) && (
                      <span style={{
                        display: 'flex', alignItems: 'center', gap: '0.2rem',
                        fontSize: '0.7rem', fontWeight: 600,
                        color: isUp ? '#10D9A0' : '#FF4F6A',
                        background: isUp ? 'rgba(16, 217, 160, 0.1)' : 'rgba(255, 79, 106, 0.1)',
                        padding: '0.15rem 0.4rem', borderRadius: '999px',
                      }}>
                        {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                        {isUp ? '+' : ''}{change}
                      </span>
                    )}
                  </div>
                </td>

                {/* Confidence */}
                <td style={{ padding: '1rem' }}>
                  {row.lower && row.upper ? (
                    <div>
                      <span style={{ fontSize: '0.8rem', color: '#4A6285' }}>
                        Rs. {row.lower} – Rs. {row.upper}
                      </span>
                    </div>
                  ) : (
                    <span style={{ fontSize: '0.8rem', color: '#4A6285' }}>± {row.confidence} Rs</span>
                  )}
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </motion.table>
    </div>
  );
}
