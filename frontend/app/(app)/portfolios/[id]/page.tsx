"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import * as api from "@/services/api";
import { ApiError } from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import { Chart } from "@/components/Chart";
import { StatCard } from "@/components/ui/StatCard";
import {
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/States";
import {
  fmtCurrency,
  fmtDate,
  fmtNumber,
  fmtPercent,
  liquidityTone,
  ratingTone,
  signClass,
} from "@/lib/format";

export default function PortfolioDetailPage() {
  const params = useParams();
  const id = String(params?.id ?? "");
  const portfolio = useAsync(
    () => api.getPortfolio(id),
    [id],
    Boolean(id)
  );

  return (
    <div>
      <PageHeader
        title={portfolio.data?.name ?? "Portfolio"}
        description={portfolio.data?.description ?? "Portfolio detail"}
        action={
          <Link
            href="/portfolios"
            className="text-sm text-accent hover:underline"
          >
            ← Back to portfolios
          </Link>
        }
      />

      {portfolio.loading ? (
        <LoadingState label="Loading portfolio…" />
      ) : portfolio.error ? (
        <ErrorState message={portfolio.error} onRetry={portfolio.reload} />
      ) : !portfolio.data ? (
        <EmptyState title="Portfolio not found" />
      ) : (
        <Tabs
          items={[
            {
              id: "holdings",
              label: "Holdings",
              content: (
                <HoldingsTab
                  id={id}
                  holdings={portfolio.data.holdings ?? []}
                  onChanged={portfolio.reload}
                />
              ),
            },
            { id: "risk", label: "Risk", content: <RiskTab id={id} /> },
            {
              id: "cashflows",
              label: "Cash Flows",
              content: <CashflowsTab id={id} />,
            },
            {
              id: "liquidity",
              label: "Liquidity",
              content: <LiquidityTab id={id} />,
            },
          ]}
        />
      )}
    </div>
  );
}

function HoldingsTab({
  id,
  holdings,
  onChanged,
}: {
  id: string;
  holdings: import("@/lib/types").Holding[];
  onChanged: () => void;
}) {
  const [instrumentId, setInstrumentId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [buyDate, setBuyDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.addHolding(id, {
        instrument_id: instrumentId.trim(),
        quantity: Number(quantity),
        buy_price: Number(buyPrice),
        buy_date: buyDate,
      });
      setInstrumentId("");
      setQuantity("");
      setBuyPrice("");
      setBuyDate("");
      onChanged();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to add holding"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Card>
          <CardHeader
            title="Holdings"
            subtitle={`${holdings.length} positions`}
          />
          {!holdings.length ? (
            <EmptyState
              title="No holdings"
              description="Add a holding using the form."
            />
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Instrument</TH>
                  <TH align="right">Qty</TH>
                  <TH align="right">Buy Price</TH>
                  <TH align="right">Mkt Value</TH>
                  <TH align="right">Weight</TH>
                  <TH align="right">P/L</TH>
                  <TH>Rating</TH>
                </TR>
              </THead>
              <TBody>
                {holdings.map((h) => {
                  const gl = h.gain_loss ?? h.analytics?.gain_loss ?? null;
                  const mv =
                    h.market_value ?? h.analytics?.market_value ?? null;
                  return (
                    <TR key={h.id}>
                      <TD>
                        <Link
                          href={`/instruments/${h.instrument_id}`}
                          className="font-medium text-accent hover:underline"
                        >
                          {h.instrument_name ?? h.name ?? h.instrument_id}
                        </Link>
                        {h.issuer_name ? (
                          <div className="text-xs text-slate-500">
                            {h.issuer_name}
                          </div>
                        ) : null}
                      </TD>
                      <TD align="right">{fmtNumber(h.quantity, 0)}</TD>
                      <TD align="right">{fmtNumber(h.buy_price)}</TD>
                      <TD align="right">{fmtCurrency(mv)}</TD>
                      <TD align="right">{fmtPercent(h.weight)}</TD>
                      <TD align="right" className={signClass(gl)}>
                        {fmtCurrency(gl)}
                      </TD>
                      <TD>
                        {h.rating ? (
                          <Badge tone={ratingTone(h.rating)}>
                            {h.rating}
                          </Badge>
                        ) : (
                          "—"
                        )}
                      </TD>
                    </TR>
                  );
                })}
              </TBody>
            </Table>
          )}
        </Card>
      </div>

      <div>
        <Card>
          <CardHeader title="Add holding" />
          <CardBody>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <Label htmlFor="instrument_id">Instrument ID</Label>
                <Input
                  id="instrument_id"
                  required
                  value={instrumentId}
                  onChange={(e) => setInstrumentId(e.target.value)}
                  placeholder="instrument uuid"
                />
              </div>
              <div>
                <Label htmlFor="quantity">Quantity</Label>
                <Input
                  id="quantity"
                  type="number"
                  min={0}
                  step="any"
                  required
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="buy_price">Buy price</Label>
                <Input
                  id="buy_price"
                  type="number"
                  min={0}
                  step="any"
                  required
                  value={buyPrice}
                  onChange={(e) => setBuyPrice(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="buy_date">Buy date</Label>
                <Input
                  id="buy_date"
                  type="date"
                  required
                  value={buyDate}
                  onChange={(e) => setBuyDate(e.target.value)}
                />
              </div>
              {error ? (
                <div className="rounded-md border border-negative/30 bg-negative/10 px-3 py-2 text-xs text-negative">
                  {error}
                </div>
              ) : null}
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Adding…" : "Add holding"}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function RiskTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.getPortfolioRisk(id),
    [id]
  );
  if (loading) return <LoadingState label="Computing risk…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <EmptyState title="No risk data" />;

  const stress = data.stress ?? [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard label="Duration" value={fmtNumber(data.duration, 2)} />
        <StatCard label="Convexity" value={fmtNumber(data.convexity, 2)} />
        <StatCard label="DV01" value={fmtCurrency(data.dv01)} sub="per 1bp" />
      </div>

      <Card>
        <CardHeader
          title="Stress Scenarios"
          subtitle="Hypothetical P/L under simulated shocks"
        />
        {!stress.length ? (
          <EmptyState title="No stress scenarios" />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Scenario</TH>
                <TH>Description</TH>
                <TH align="right">P/L</TH>
                <TH align="right">P/L %</TH>
              </TR>
            </THead>
            <TBody>
              {stress.map((s, i) => (
                <TR key={i}>
                  <TD className="font-medium text-slate-100">{s.name}</TD>
                  <TD className="max-w-[320px] whitespace-normal text-xs text-slate-400">
                    {s.description}
                  </TD>
                  <TD align="right" className={signClass(s.pnl)}>
                    {fmtCurrency(s.pnl)}
                  </TD>
                  <TD align="right" className={signClass(s.pnl_pct)}>
                    {fmtPercent(s.pnl_pct)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      {data.issuer_concentration?.length ? (
        <Card>
          <CardHeader title="Issuer Concentration" />
          <Table>
            <THead>
              <TR>
                <TH>Issuer</TH>
                <TH align="right">Weight</TH>
              </TR>
            </THead>
            <TBody>
              {data.issuer_concentration.map((it, i) => (
                <TR key={i}>
                  <TD>{it.issuer}</TD>
                  <TD align="right">{fmtPercent(it.weight)}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </Card>
      ) : null}
    </div>
  );
}

function CashflowsTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.getPortfolioCashflows(id),
    [id]
  );
  if (loading) return <LoadingState label="Loading cash flows…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  const calendar = data?.calendar ?? [];
  const upcoming = data?.upcoming ?? [];
  if (!calendar.length && !upcoming.length)
    return <EmptyState title="No cash flows" />;

  return (
    <div className="space-y-6">
      {calendar.length ? (
        <Card>
          <CardHeader
            title="Cash-Flow Calendar"
            subtitle="Coupon and principal by month"
          />
          <CardBody>
            <Chart
              data={[
                {
                  type: "bar",
                  name: "Coupon",
                  x: calendar.map((c) => c.month),
                  y: calendar.map((c) => c.coupon),
                  marker: { color: "#3b82f6" },
                },
                {
                  type: "bar",
                  name: "Principal",
                  x: calendar.map((c) => c.month),
                  y: calendar.map((c) => c.principal),
                  marker: { color: "#22c55e" },
                },
              ]}
              layout={{ barmode: "stack" }}
              height={320}
            />
          </CardBody>
        </Card>
      ) : null}

      {upcoming.length ? (
        <Card>
          <CardHeader title="Upcoming Payments" />
          <Table>
            <THead>
              <TR>
                <TH>Pay Date</TH>
                <TH>Kind</TH>
                <TH align="right">Amount</TH>
              </TR>
            </THead>
            <TBody>
              {upcoming.map((cf, i) => (
                <TR key={i}>
                  <TD>{fmtDate(cf.pay_date)}</TD>
                  <TD>
                    <Badge
                      tone={cf.kind === "principal" ? "accent" : "neutral"}
                    >
                      {cf.kind}
                    </Badge>
                  </TD>
                  <TD align="right">{fmtCurrency(cf.amount)}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </Card>
      ) : null}
    </div>
  );
}

function LiquidityTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.getPortfolioLiquidity(id),
    [id]
  );
  if (loading) return <LoadingState label="Loading liquidity…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <EmptyState title="No liquidity data" />;

  const buckets = data.buckets ?? {
    high: 0,
    moderate: 0,
    low: 0,
    insufficient: 0,
  };
  const illiquid = data.illiquid_holdings ?? [];

  const bucketRows: { label: string; value: number; tone: "positive" | "warning" | "negative" | "neutral" }[] = [
    { label: "High", value: buckets.high ?? 0, tone: "positive" },
    { label: "Moderate", value: buckets.moderate ?? 0, tone: "warning" },
    { label: "Low", value: buckets.low ?? 0, tone: "negative" },
    {
      label: "Insufficient",
      value: buckets.insufficient ?? 0,
      tone: "neutral",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {bucketRows.map((b) => (
          <StatCard
            key={b.label}
            label={`${b.label} liquidity`}
            value={fmtPercent(b.value)}
            tone={
              b.tone === "negative"
                ? "negative"
                : b.tone === "warning"
                ? "warning"
                : b.tone === "positive"
                ? "positive"
                : "neutral"
            }
          />
        ))}
      </div>

      <Card className="px-4 py-3">
        <div className="text-xs text-slate-400">
          Estimated liquidation time
        </div>
        <div className="mt-1 text-xl font-semibold tabular text-slate-100">
          {data.est_liquidation_days != null
            ? `${fmtNumber(data.est_liquidation_days, 1)} days`
            : "—"}
        </div>
      </Card>

      <Card>
        <CardHeader title="Illiquid Holdings" />
        {!illiquid.length ? (
          <EmptyState title="No illiquid holdings flagged" />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Holding</TH>
                <TH>Class</TH>
                <TH align="right">Weight</TH>
              </TR>
            </THead>
            <TBody>
              {illiquid.map((h, i) => (
                <TR key={i}>
                  <TD>{h.name}</TD>
                  <TD>
                    {h.liquidity_class ? (
                      <Badge tone={liquidityTone(h.liquidity_class)}>
                        {h.liquidity_class}
                      </Badge>
                    ) : (
                      "—"
                    )}
                  </TD>
                  <TD align="right">
                    {h.weight != null ? fmtPercent(h.weight) : "—"}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      {data.disclaimer ? (
        <p className="text-xs text-slate-500">{data.disclaimer}</p>
      ) : null}
    </div>
  );
}
