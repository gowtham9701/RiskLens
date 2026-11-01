// Formatting helpers for monetary, percentage and date values. All guard
// against null/undefined/NaN so the UI never crashes on missing data.

export function fmtCurrency(
  value: number | null | undefined,
  opts: { compact?: boolean; currency?: string } = {}
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const { compact = false, currency = "USD" } = opts;
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      notation: compact ? "compact" : "standard",
      maximumFractionDigits: compact ? 2 : 2,
    }).format(value);
  } catch {
    return `$${value.toFixed(2)}`;
  }
}

export function fmtNumber(
  value: number | null | undefined,
  digits = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function fmtPercent(
  value: number | null | undefined,
  digits = 2,
  alreadyPercent = true
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const v = alreadyPercent ? value : value * 100;
  return `${v.toFixed(digits)}%`;
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function signClass(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value))
    return "text-slate-300";
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-slate-300";
}

export function severityTone(
  severity: string | null | undefined
): "positive" | "negative" | "warning" | "neutral" | "accent" {
  const s = (severity ?? "").toLowerCase();
  if (["critical", "high", "severe"].includes(s)) return "negative";
  if (["medium", "moderate", "warning"].includes(s)) return "warning";
  if (["low", "info"].includes(s)) return "accent";
  if (["resolved", "ok", "cleared"].includes(s)) return "positive";
  return "neutral";
}

export function ratingTone(
  rating: string | null | undefined
): "positive" | "warning" | "negative" | "neutral" {
  if (!rating) return "neutral";
  const r = rating.toUpperCase();
  if (r.startsWith("AAA") || r.startsWith("AA") || r.startsWith("A"))
    return "positive";
  if (r.startsWith("BBB") || r.startsWith("BB")) return "warning";
  if (r.startsWith("B") || r.startsWith("C") || r.startsWith("D"))
    return "negative";
  return "neutral";
}

export function liquidityTone(
  cls: string | null | undefined
): "positive" | "warning" | "negative" | "neutral" {
  const c = (cls ?? "").toLowerCase();
  if (c.includes("high")) return "positive";
  if (c.includes("moderate") || c.includes("medium")) return "warning";
  if (c.includes("low") || c.includes("insufficient") || c.includes("illiquid"))
    return "negative";
  return "neutral";
}
