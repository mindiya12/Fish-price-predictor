"use client";

import { useEffect, type CSSProperties } from "react";
import { animate, motion, useMotionValue, useTransform, useReducedMotion } from "framer-motion";

type AnimatedNumberProps = {
  value: number;
  duration?: number;     // seconds
  decimals?: number;     // 0 for Rs.
  className?: string;
  style?: CSSProperties;
};

export default function AnimatedNumber({
  value,
  duration = 0.8,
  decimals = 0,
  className,
  style,
}: AnimatedNumberProps) {
  const reduceMotion = useReducedMotion();
  const mv = useMotionValue(0);

  const display = useTransform(mv, (latest) => {
    const num = Number(latest);
    return num.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  });

  useEffect(() => {
    if (reduceMotion) return;

    const controls = animate(mv, value, {
      duration,
      ease: "easeOut",
    });

    return () => controls.stop();
  }, [mv, value, duration, reduceMotion]);

  if (reduceMotion) {
    return (
      <span className={className} style={style}>
        {value.toLocaleString(undefined, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        })}
      </span>
    );
  }

  return (
    <motion.span className={className} style={style}>
      {display}
    </motion.span>
  );
}
