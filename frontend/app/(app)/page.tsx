"use client";

import { useMemo, useState } from "react";
import * as api from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Chart } from "@/components/Chart";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/States";
import {
  fmtCurrency,
  fmtNumber,
  fmtPercent,
  severityTone,
} from "@/lib/format";
import type { AllocationSlice, MaturityBucket } from "@/lib/types";

function asSlices(
  input: AllocationSlice[] | undefined | null
): AllocationSlice[] {
  if (!Array.isArray(input)) return [];
  return input.filter((s) => s && typeof s.value === "number");
}

export default function DashboardPage() {
  const portfolios = useAsync(() => api.listPortfolios(), []);
  const [selected, setSelected] = useState<string>("");

  const items = portfolios.data?.items ?? [];
  const activeId = selected || items[0]?.id || "";

  const dashboard = useAsync(
    () => api.getDashboard(activeId),
    [activeId],
    Boolean(activeId)
  );

  const d = dashboard.data;

  const allocPie = useMemo(() => {
    const slices = asSlices(d?.allocations_by_category);
    if (!slices.length) return null;
    return [
      {
        type: "pie" as const,
        labels: slices.map((s) => s.label),
        values: slices.map((s) => s.value),
        hole: 0.55,
        textinfo: "label+percent",
        textfont: { size: 10 },
      },
    ];
  }, [d]);

  const ratingBar = useMemo(() => {
    const slices = asSlices(d?.rating_distribution);
    if (!slices.length) return null;
    return [
      {
        type: "bar" as const,
        x: slices.map((s) => s.label),
        y: slices.map((s) => s.value),
        marker: { color: "#3b82f6" },
      },
    ];
  }, [d]);

  const maturityBar = useMemo(() => {
    const ladder: MaturityBucket[] = Array.isArray(d?.maturity_ladder)
      ? (d!.maturity_ladder as MaturityBucket[])
      : [];
    if (!ladder.length) return null;
    return [
      {
        type: "bar" as const,
        x: ladder.map((s) => s.label),
        y: ladder.map((s) => s.value),
        marker: { color: "#22c55e" },
      },
    ];
  }, [d]);

  return (
    <div>
      <PageHeader
        title="Portfolio Dashboard"
        description="Key risk and return indicators for your selected simulated portfolio."
        action={
          items.length ? (
            <div className="w-64">
              <Select
                value={activeId}
                onChange={(e) => setSelected(e.target.value)}
                aria-label="Select portfolio"
              >
                {items.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </div>
          ) : null
        }
      />

      {portfolios.loading ? (
        <LoadingState label="Loading portfolios…" />
      ) : portfolios.error ? (
        <ErrorState message={portfolios.error} onRetry={portfolios.reload} />
      ) : !items.length ? (
        <EmptyState
          title="No portfolios yet"
          description="Create a portfolio or use the Portfolio Builder to get started."
        />
      ) : dashboard.loading ? (
        <LoadingState label="Computing analytics…" />
      ) : dashboard.error ? (
        <ErrorState message={dashboard.error} onRetry={dashboard.reload} />
      ) : !d ? (
        <EmptyState title="No dashboard data" />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
            <StatCard
              label="Total Value"
              value={fmtCurrency(d.total_value)}
            />
            <StatCard
              label="Unrealised P/L"
              value={fmtCurrency(d.unrealised_gain_loss)}
              sub={
                d.gain_loss_pct != null
                  ? fmtPercent(d.gain_loss_pct)
                  : undefined
              }
              tone={
                (d.unrealised_gain_loss ?? 0) > 0
                  ? "positive"
                  : (d.unrealised_gain_loss ?? 0) < 0
                  ? "negative"
                  : "neutral"
              }
            />
            <StatCard
              label="Weighted Yield"
              value={fmtPercent(d.weighted_yield)}
            />
            <StatCard
              label="Annual Income"
              value={fmtCurrency(d.annual_income)}
            />
            <StatCard
              label="Mod. Duration"
              value={fmtNumber(d.modified_duration, 2)}
              sub="years"
            />
            <StatCard label="DV01" value={fmtCurrency(d.dv01)} sub="per 1bp" />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card>
              <CardHeader
                title="Asset Allocation"
                subtitle="By category"
              />
              <CardBody>
                {allocPie ? (
                  <Chart data={allocPie} height={280} />
                ) : (
                  <EmptyState title="No allocation data" />
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader
                title="Credit Rating"
                subtitle="Distribution by weight"
              />
              <CardBody>
                {ratingBar ? (
                  <Chart data={ratingBar} height={280} />
                ) : (
                  <EmptyState title="No rating data" />
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader
                title="Maturity Ladder"
                subtitle="Value by maturity bucket"
              />
              <CardBody>
                {maturityBar ? (
                  <Chart data={maturityBar} height={280} />
                ) : (
                  <EmptyState title="No maturity data" />
                )}
              </CardBody>
            </Card>
          </div>

          <RiskSummary data={d} />
        </div>
      )}
    </div>
  );
}

function RiskSummary({
  data,
}: {
  data: import("@/lib/types").DashboardKPIs;
}) {
  const issuers = data.issuer_concentration ?? [];
  const lowLiq = data.low_liquidity_holdings ?? [];
  const downgrades = data.downgrade_alerts ?? [];

  return (
    <Card>
      <CardHeader
        title="Risk Summary"
        subtitle="Concentration, liquidity and credit-event watch"
      />
      <CardBody>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Issuer Concentration
            </div>
            {issuers.length ? (
              <ul className="space-y-1.5">
                {issuers.slice(0, 6).map((it, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="truncate text-slate-200">
                      {it.issuer}
                    </span>
                    <span className="tabular text-slate-300">
                      {fmtPercent(it.weight)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No concentration data.</p>
            )}
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Low-Liquidity Holdings
            </div>
            {lowLiq.length ? (
              <ul className="space-y-1.5">
                {lowLiq.slice(0, 6).map((it, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-2 text-sm"
                  >
                    <span className="truncate text-slate-200">{it.name}</span>
                    <Badge tone="warning">{it.liquidity_class}</Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">
                No low-liquidity holdings flagged.
              </p>
            )}
          </div>

          <div>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              Downgrade Alerts
            </div>
            {downgrades.length ? (
              <ul className="space-y-1.5">
                {downgrades.slice(0, 6).map((it, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <Badge tone={severityTone(it.severity)}>
                      {it.severity ?? "alert"}
                    </Badge>
                    <span className="text-slate-300">{it.message}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No downgrade alerts.</p>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
