import { cn } from "@/lib/cn";

type Tone =
  | "neutral"
  | "positive"
  | "negative"
  | "warning"
  | "accent";

const tones: Record<Tone, string> = {
  neutral: "bg-navy-700 text-slate-300 border-navy-600",
  positive: "bg-positive/15 text-positive border-positive/30",
  negative: "bg-negative/15 text-negative border-negative/30",
  warning: "bg-warning/15 text-warning border-warning/30",
  accent: "bg-accent/15 text-accent border-accent/30",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
