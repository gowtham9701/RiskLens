"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import * as api from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import { Chart } from "@/components/Chart";
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
  fmtDateTime,
  fmtNumber,
  fmtPercent,
  liquidityTone,
  ratingTone,
} from "@/lib/format";
import type {
  InstrumentDetail,
  LiquidityComponent,
} from "@/lib/types";

function Field({
  label,
  value,
  className,
}: {
  label: string;
  value: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-0.5 text-sm text-slate-100">{value}</div>
    </div>
  );
}

export default function InstrumentDetailPage() {
  const params = useParams();
  const id = String(params?.id ?? "");
  const { data, loading, error, reload } = useAsync(
    () => api.getInstrument(id),
    [id],
    Boolean(id)
  );

  return (
    <div>
      <PageHeader
        title={data?.name ?? "Instrument"}
        description={
          data
            ? `${data.isin} · ${data.issuer_name}`
            : "Loading instrument details…"
        }
        action={
          <Link
            href="/instruments"
            className="text-sm text-accent hover:underline"
          >
            ← Back to instruments
          </Link>
        }
      />

      {loading ? (
        <LoadingState label="Loading instrument…" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !data ? (
        <EmptyState title="Instrument not found" />
      ) : (
        <Card>
          <CardBody>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <Badge tone={data.is_government ? "accent" : "neutral"}>
                {data.category}
              </Badge>
              {data.rating ? (
                <Badge tone={ratingTone(data.rating)}>
                  {data.rating}
                  {data.rating_agency ? ` · ${data.rating_agency}` : ""}
                </Badge>
              ) : null}
              {data.liquidity_class ? (
                <Badge tone={liquidityTone(data.liquidity_class)}>
                  {data.liquidity_class}
                </Badge>
              ) : null}
              {data.sector ? (
                <Badge tone="neutral">{data.sector}</Badge>
              ) : null}
            </div>

            <Tabs
              items={[
                {
                  id: "overview",
                  label: "Overview",
                  content: <OverviewTab d={data} />,
                },
                {
                  id: "cashflows",
                  label: "Cash Flows",
                  content: <CashflowsTab id={id} />,
                },
                {
                  id: "prices",
                  label: "Prices",
                  content: <PricesTab id={id} />,
                },
                {
                  id: "ratings",
                  label: "Ratings",
                  content: <RatingsTab id={id} />,
                },
                {
                  id: "liquidity",
                  label: "Liquidity",
                  content: <LiquidityTab id={id} />,
                },
                {
                  id: "news",
                  label: "News",
                  content: <NewsTab id={id} />,
                },
              ]}
            />
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function OverviewTab({ d }: { d: InstrumentDetail }) {
  const a = d.analytics ?? {};
  const ytm = d.ytm ?? a.ytm;
  const dur = d.modified_duration ?? a.modified_duration;
  const convexity = d.convexity ?? a.convexity;
  const dv01 = d.dv01 ?? a.dv01;

  return (
    <div className="space-y-6">
      <div>
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Terms
        </h4>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <Field label="ISIN" value={d.isin} />
          <Field label="Issuer" value={d.issuer_name} />
          <Field label="Sector" value={d.sector ?? "—"} />
          <Field label="Seniority" value={d.seniority ?? "—"} />
          <Field label="Coupon" value={fmtPercent(d.coupon_rate)} />
          <Field
            label="Coupon Frequency"
            value={d.coupon_frequency ?? "—"}
          />
          <Field label="Day Count" value={d.day_count ?? "—"} />
          <Field label="Issue Date" value={fmtDate(d.issue_date)} />
          <Field label="Maturity" value={fmtDate(d.maturity_date)} />
          <Field label="Face Value" value={fmtCurrency(d.face_value)} />
          <Field
            label="Callable"
            value={d.callable ? "Yes" : "No"}
          />
          <Field label="Puttable" value={d.puttable ? "Yes" : "No"} />
          <Field label="Secured" value={d.secured ? "Yes" : "No"} />
        </div>
      </div>

      <div>
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Computed Analytics
        </h4>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          <Field label="Clean Price" value={fmtNumber(d.clean_price)} />
          <Field label="Dirty Price" value={fmtNumber(d.dirty_price)} />
          <Field
            label="Accrued Interest"
            value={fmtNumber(d.accrued_interest)}
          />
          <Field label="YTM" value={fmtPercent(ytm)} />
          <Field
            label="Current Yield"
            value={fmtPercent(d.current_yield)}
          />
          <Field label="YTC" value={fmtPercent(d.ytc)} />
          <Field label="Mod. Duration" value={fmtNumber(dur)} />
          <Field label="Convexity" value={fmtNumber(convexity)} />
          <Field label="DV01" value={fmtCurrency(dv01)} />
        </div>
      </div>
    </div>
  );
}

function CashflowsTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.instrumentCashflows(id),
    [id]
  );
  const items = data?.items ?? [];
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!items.length) return <EmptyState title="No cash flows" />;
  return (
    <Table>
      <THead>
        <TR>
          <TH>Pay Date</TH>
          <TH>Kind</TH>
          <TH align="right">Amount</TH>
        </TR>
      </THead>
      <TBody>
        {items.map((cf, i) => (
          <TR key={i}>
            <TD>{fmtDate(cf.pay_date)}</TD>
            <TD>
              <Badge tone={cf.kind === "principal" ? "accent" : "neutral"}>
                {cf.kind}
              </Badge>
            </TD>
            <TD align="right">{fmtCurrency(cf.amount)}</TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}

function PricesTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.instrumentPrices(id),
    [id]
  );
  const items = data?.items ?? [];
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!items.length) return <EmptyState title="No price history" />;

  const sorted = [...items].sort(
    (a, b) => new Date(a.price_date).getTime() - new Date(b.price_date).getTime()
  );

  return (
    <Chart
      data={[
        {
          type: "scatter",
          mode: "lines",
          x: sorted.map((p) => p.price_date),
          y: sorted.map((p) => p.clean_price),
          line: { color: "#3b82f6", width: 2 },
          name: "Clean price",
        },
      ]}
      height={340}
    />
  );
}

function RatingsTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.instrumentRatings(id),
    [id]
  );
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  const current = data?.current;
  const history = data?.history ?? [];
  if (!current && !history.length)
    return <EmptyState title="No rating data" />;

  return (
    <div className="space-y-6">
      {current ? (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Current Rating
          </h4>
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone={ratingTone(current.rating)}>
              {current.rating ?? "—"}
            </Badge>
            {current.agency ? (
              <span className="text-sm text-slate-300">{current.agency}</span>
            ) : null}
            {current.outlook ? (
              <span className="text-xs text-slate-400">
                Outlook: {current.outlook}
              </span>
            ) : null}
            {current.rated_at ? (
              <span className="text-xs text-slate-500">
                {fmtDate(current.rated_at)}
              </span>
            ) : null}
          </div>
        </div>
      ) : null}

      {history.length ? (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Rating History
          </h4>
          <Table>
            <THead>
              <TR>
                <TH>Date</TH>
                <TH>Agency</TH>
                <TH>Rating</TH>
                <TH>Action</TH>
                <TH>Outlook</TH>
              </TR>
            </THead>
            <TBody>
              {history.map((h, i) => (
                <TR key={i}>
                  <TD>{fmtDate(h.rated_at)}</TD>
                  <TD>{h.agency ?? "—"}</TD>
                  <TD>
                    <Badge tone={ratingTone(h.rating)}>
                      {h.rating ?? "—"}
                    </Badge>
                  </TD>
                  <TD>{h.action ?? "—"}</TD>
                  <TD>{h.outlook ?? "—"}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      ) : null}
    </div>
  );
}

function LiquidityTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.instrumentLiquidity(id),
    [id]
  );
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <EmptyState title="No liquidity data" />;

  const components: LiquidityComponent[] = Array.isArray(data.components)
    ? data.components
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-6">
        <div>
          <div className="text-xs text-slate-500">Liquidity Score</div>
          <div className="mt-0.5 text-2xl font-semibold tabular text-slate-100">
            {fmtNumber(data.liquidity_score, 1)}
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Classification</div>
          <div className="mt-1">
            <Badge
              tone={liquidityTone(
                data.liquidity_class ?? data.classification
              )}
            >
              {data.liquidity_class ?? data.classification ?? "—"}
            </Badge>
          </div>
        </div>
      </div>

      {components.length ? (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Score Components
          </h4>
          <Table>
            <THead>
              <TR>
                <TH>Component</TH>
                <TH align="right">Value</TH>
                <TH align="right">Weight</TH>
              </TR>
            </THead>
            <TBody>
              {components.map((c, i) => (
                <TR key={i}>
                  <TD>{c.name}</TD>
                  <TD align="right">{fmtNumber(c.value, 1)}</TD>
                  <TD align="right">
                    {c.weight != null ? fmtPercent(c.weight) : "—"}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      ) : null}

      {data.disclaimer ? (
        <p className="text-xs text-slate-500">{data.disclaimer}</p>
      ) : null}
    </div>
  );
}

function NewsTab({ id }: { id: string }) {
  const { data, loading, error, reload } = useAsync(
    () => api.instrumentNews(id),
    [id]
  );
  const items = data?.items ?? [];
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!items.length) return <EmptyState title="No news" />;

  const impactTone = (
    impact: string | null
  ): "positive" | "negative" | "warning" | "neutral" => {
    const s = (impact ?? "").toLowerCase();
    if (s.includes("positive") || s.includes("upgrade")) return "positive";
    if (s.includes("negative") || s.includes("downgrade")) return "negative";
    if (s.includes("neutral")) return "neutral";
    if (s) return "warning";
    return "neutral";
  };

  return (
    <div className="space-y-3">
      {items.map((n) => (
        <Card key={n.id} className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-slate-100">
                {n.headline}
              </div>
              <div className="mt-0.5 text-xs text-slate-500">
                {n.source} · {fmtDateTime(n.published_at)}
              </div>
            </div>
            {n.risk_impact ? (
              <Badge tone={impactTone(n.risk_impact)}>{n.risk_impact}</Badge>
            ) : null}
          </div>
          {n.summary ? (
            <p className="mt-2 text-sm text-slate-300">{n.summary}</p>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-2">
            {n.category ? <Badge tone="neutral">{n.category}</Badge> : null}
            {n.issuer_name ? (
              <Badge tone="neutral">{n.issuer_name}</Badge>
            ) : null}
          </div>
        </Card>
      ))}
    </div>
  );
}
