"use client";

import * as api from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/States";
import { fmtCurrency } from "@/lib/format";

function DownloadIcon() {
  return (
    <svg
      className="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </svg>
  );
}

export default function ReportsPage() {
  const { data, loading, error, reload } = useAsync(
    () => api.listPortfolios(),
    []
  );
  const items = data?.items ?? [];

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Download simulated portfolio reports in Excel or PDF."
      />

      <Card>
        <CardHeader title="Portfolios" />
        {loading ? (
          <LoadingState label="Loading portfolios…" />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !items.length ? (
          <EmptyState
            title="No portfolios"
            description="Create a portfolio to generate reports."
          />
        ) : (
          <div className="divide-y divide-navy-700">
            {items.map((p) => (
              <div
                key={p.id}
                className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
              >
                <div>
                  <div className="text-sm font-medium text-slate-100">
                    {p.name}
                  </div>
                  <div className="text-xs text-slate-500">
                    {p.total_value != null
                      ? fmtCurrency(p.total_value)
                      : "Fixed-income portfolio"}
                  </div>
                </div>
                <div className="flex gap-2">
                  <a
                    href={api.reportUrl(p.id, "xlsx")}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-md border border-navy-600 bg-navy-700 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-navy-600"
                  >
                    <DownloadIcon />
                    Excel
                  </a>
                  <a
                    href={api.reportUrl(p.id, "pdf")}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-md border border-navy-600 bg-navy-700 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-navy-600"
                  >
                    <DownloadIcon />
                    PDF
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <p className="mt-4 text-xs text-slate-500">
        Report downloads require the backend to be running and an
        authenticated session. Files open in a new tab.
      </p>
    </div>
  );
}
