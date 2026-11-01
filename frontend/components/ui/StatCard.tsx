import { cn } from "@/lib/cn";
import { Card } from "./Card";

export function StatCard({
  label,
  value,
  sub,
  tone = "neutral",
  className,
}: {
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  tone?: "neutral" | "positive" | "negative" | "warning";
  className?: string;
}) {
  const valueTone =
    tone === "positive"
      ? "text-positive"
      : tone === "negative"
      ? "text-negative"
      : tone === "warning"
      ? "text-warning"
      : "text-slate-100";
  return (
    <Card className={cn("px-4 py-3", className)}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className={cn("mt-1 text-2xl font-semibold tabular", valueTone)}>
        {value}
      </div>
      {sub ? <div className="mt-1 text-xs text-slate-400">{sub}</div> : null}
    </Card>
  );
}
