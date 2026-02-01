import type { ForecastPoint } from "@/types";

export const detailedForecast7Days: ForecastPoint[] = [
  { day: 1, dateLabel: "Jan 1", prediction: 715, confidence: 30, lower: 685, upper: 745, changePct: 1.4 },
  { day: 2, dateLabel: "Jan 2", prediction: 662, confidence: 54, lower: 608, upper: 716, changePct: -7.4 },
  { day: 3, dateLabel: "Jan 3", prediction: 682, confidence: 63, lower: 619, upper: 745, changePct: 3.0 },
  { day: 4, dateLabel: "Jan 4", prediction: 709, confidence: 73, lower: 636, upper: 782, changePct: 4.0 },
  { day: 5, dateLabel: "Jan 5", prediction: 691, confidence: 81, lower: 610, upper: 772, changePct: -2.5 },
  { day: 6, dateLabel: "Jan 6", prediction: 703, confidence: 87, lower: 616, upper: 790, changePct: 1.7 },
  { day: 7, dateLabel: "Jan 7", prediction: 707, confidence: 92, lower: 615, upper: 799, changePct: 0.6 },
];


// TODO BACKEND INTEGRATION:
// Replace with API data (7-day detailed forecast) once backend is ready.
// Suggested: GET /api/forecast/latest?fish=balaya (or your final endpoint).
