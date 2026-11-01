import { cn } from "@/lib/cn";

export function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn("h-5 w-5 animate-spin text-accent", className)}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}

export function LoadingState({
  label = "Loading…",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-center gap-3 py-12 text-sm text-slate-400",
        className
      )}
    >
      <Spinner />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title = "Nothing to show",
  description,
  action,
  className,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-navy-700 py-12 text-center",
        className
      )}
    >
      <div className="text-sm font-medium text-slate-300">{title}</div>
      {description ? (
        <p className="max-w-sm text-xs text-slate-500">{description}</p>
      ) : null}
      {action}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
  className,
}: {
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border border-negative/30 bg-negative/5 py-10 text-center",
        className
      )}
    >
      <div className="text-sm font-medium text-negative">
        Something went wrong
      </div>
      <p className="max-w-md px-4 text-xs text-slate-400">
        {message ?? "Unable to load data."}
      </p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="rounded-md border border-navy-600 bg-navy-700 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-navy-600"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
