import type { Trend } from "@/types";
import AnimatedNumber from "./AnimatedNumber";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

type Props = {
  title: string;
  value: number | string;
  subtitle?: string;
  trend?: Trend;
  trendText?: string;
  unit?: string;
  duration?: number;
  decimals?: number;
  icon?: React.ReactNode;
  accentColor?: string;
};

export default function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendText,
  unit = "Rs.",
  duration = 1.0,
  decimals = 0,
  icon,
  accentColor = "#00D4FF",
}: Props) {
  const isNumber = typeof value === "number" && Number.isFinite(value);

  const trendColor =
    trend === "up" ? "#10D9A0" :
    trend === "down" ? "#FF4F6A" :
    "#7A9CC9";

  const TrendIcon =
    trend === "up" ? TrendingUp :
    trend === "down" ? TrendingDown :
    Minus;

  return (
    <div
      className="glass glass-hover"
      style={{
        padding: '1.5rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Subtle glow orb */}
      <div style={{
        position: 'absolute',
        top: '-20px',
        right: '-20px',
        width: '80px',
        height: '80px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${accentColor}18, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <p style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#4A6285' }}>
          {title}
        </p>
        {icon && (
          <div style={{
            width: '32px', height: '32px',
            borderRadius: '8px',
            background: `${accentColor}15`,
            border: `1px solid ${accentColor}25`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: accentColor,
          }}>
            {icon}
          </div>
        )}
      </div>

      {/* Value */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {isNumber ? (
          <>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#4A6285' }}>{unit}</span>
            <AnimatedNumber
              value={value}
              duration={duration}
              decimals={decimals}
              className="tabular-nums"
              style={{
                fontSize: '2.25rem',
                fontWeight: 800,
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                background: `linear-gradient(135deg, ${accentColor}, #EDF4FF)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '-0.02em',
              }}
            />
          </>
        ) : (
          <span style={{
            fontSize: '2rem',
            fontWeight: 800,
            fontFamily: "'Plus Jakarta Sans', sans-serif",
            background: `linear-gradient(135deg, ${accentColor}, #EDF4FF)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            {value}
          </span>
        )}
      </div>

      {/* Trend / Subtitle row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {trendText && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <TrendIcon size={13} color={trendColor} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: trendColor }}>{trendText}</span>
          </div>
        )}
        {subtitle && (
          <span style={{
            fontSize: '0.7rem',
            fontWeight: 500,
            color: '#4A6285',
            background: 'rgba(0, 212, 255, 0.06)',
            border: '1px solid rgba(0, 212, 255, 0.12)',
            borderRadius: '999px',
            padding: '0.2rem 0.6rem',
          }}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}
