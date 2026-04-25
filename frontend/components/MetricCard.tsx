import type { Trend } from "@/types";
import AnimatedNumber from "./AnimatedNumber";

type Props = {
  title: string;

  /**
   * Use number for count-up animation.
   * Keep string for values like "680 – 770".
   */
  value: number | string;

  subtitle?: string;
  trend?: Trend;
  trendText?: string; // e.g., "+1.4% Stable"

  /**
   * Optional: show currency/unit before number (default: "Rs.")
   * If you pass a string like "Rs. 715", set unit to "" or keep value as string.
   */
  unit?: string;

  /**
   * Count-up duration (seconds) for numeric values only.
   */
  duration?: number;

  /**
   * Decimal places for numeric values only (Rs. should be 0).
   */
  decimals?: number;
};

export default function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendText,
  unit = "Rs.",
  duration = 0.8,
  decimals = 0,
}: Props) {
  const trendColor =
    trend === "up"
      ? "text-brand-success"
      : trend === "down"
        ? "text-brand-alert"
        : "text-brand-neutral";

  const isNumber = typeof value === "number" && Number.isFinite(value);

  return (
    <div className="rounded-lg bg-white p-5 shadow-subtle ring-1 ring-black/5 transition hover:shadow-sm-elevated">
      <p className="text-xs font-semibold uppercase tracking-wide text-brand-neutral">{title}</p>

      <div className="mt-3 flex items-baseline gap-2">
        <p className="text-3xl font-bold text-brand-primary">
          {isNumber ? (
            <>
              {unit ? <span className="mr-2">{unit}</span> : null}
              <AnimatedNumber
                value={value}
                duration={duration}
                decimals={decimals}
                className="tabular-nums"
              />
            </>
          ) : (
            <span>{value}</span>
          )}
        </p>
      </div>

      {subtitle && (
        <p className="mt-3 inline-flex rounded-md bg-brand-light px-2 py-1 text-xs text-brand-secondary">
          {subtitle}
        </p>
      )}

      {trendText && <p className={`mt-3 text-sm ${trendColor}`}>{trendText}</p>}
    </div>
  );
}
