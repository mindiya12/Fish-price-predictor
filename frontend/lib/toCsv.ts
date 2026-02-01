export function toCsv<T extends Record<string, unknown>>(rows: T[]): string {
  if (!rows.length) return "";

  const headers = Object.keys(rows[0]);

  const escape = (v: unknown) => {
    const s = String(v ?? "");
    if (s.includes('"') || s.includes(",") || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const lines = [
    headers.join(","),
    ...rows.map((r) => headers.map((h) => escape(r[h])).join(",")),
  ];

  return lines.join("\n");
}
