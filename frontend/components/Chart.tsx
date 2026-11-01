"use client";

import { useEffect, useRef, useState } from "react";
import { Spinner } from "@/components/ui/States";

// A lightweight client-only Plotly wrapper. Plotly.js-dist-min is imported
// dynamically inside useEffect so it never runs during SSR (it touches the
// DOM/`self`), which would crash the server render. If the import fails we show
// a graceful fallback instead of breaking the page.

type PlotlyData = Record<string, unknown>[];
type PlotlyLayout = Record<string, unknown>;

const DARK_LAYOUT: PlotlyLayout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#cbd5e1", family: "monospace", size: 11 },
  margin: { l: 48, r: 16, t: 16, b: 40 },
  xaxis: {
    gridcolor: "#1c2740",
    zerolinecolor: "#1c2740",
    linecolor: "#263251",
  },
  yaxis: {
    gridcolor: "#1c2740",
    zerolinecolor: "#1c2740",
    linecolor: "#263251",
  },
  legend: { orientation: "h", y: -0.2, font: { size: 10 } },
  colorway: [
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#a855f7",
    "#ef4444",
    "#14b8a6",
    "#eab308",
    "#ec4899",
  ],
};

export function Chart({
  data,
  layout,
  height = 280,
  className,
}: {
  data: PlotlyData;
  layout?: PlotlyLayout;
  height?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading"
  );

  useEffect(() => {
    let cancelled = false;
    const node = ref.current;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let plotly: any = null;

    async function render() {
      try {
        const mod = await import("plotly.js-dist-min");
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        plotly = (mod as any).default ?? mod;
        if (cancelled || !node) return;
        await plotly.react(
          node,
          data,
          { ...DARK_LAYOUT, ...layout, autosize: true },
          { responsive: true, displayModeBar: false }
        );
        if (!cancelled) setStatus("ready");
      } catch {
        if (!cancelled) setStatus("error");
      }
    }

    render();

    return () => {
      cancelled = true;
      if (plotly && node) {
        try {
          plotly.purge(node);
        } catch {
          /* noop */
        }
      }
    };
  }, [data, layout]);

  return (
    <div className={className} style={{ position: "relative", height }}>
      {status === "loading" ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <Spinner />
        </div>
      ) : null}
      {status === "error" ? (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-500">
          Chart unavailable
        </div>
      ) : null}
      <div ref={ref} style={{ width: "100%", height }} />
    </div>
  );
}
