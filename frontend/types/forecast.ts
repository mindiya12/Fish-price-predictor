export type Trend = "up" | "down" | "neutral";

export type ForecastPoint = {
  day: number;
  dateLabel: string; // e.g. "Jan 1"
  prediction: number; // Rs
  confidence: number; // +/- Rs
  changePct?: number; // optional for MVP
  lower?: number; // prediction - confidence (optional)
  upper?: number; // prediction + confidence (optional)
};
