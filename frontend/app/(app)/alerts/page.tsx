"use client";

import Link from "next/link";
import * as api from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
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
import { fmtCurrency, fmtDateTime, severityTone } from "@/lib/format";

export default function AlertsPage() {
  const { data, loading, error, reload } = useAsync(
    () => api.listAlerts(),
    []
  );
  const items = data?.items ?? [];

  return (
    <div>
      <PageHeader
        title="Alerts"
        description="Simulated risk triggers across instruments and portfolios."
      />

      <Card>
        {loading ? (
          <LoadingState label="Loading alerts…" />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !items.length ? (
          <EmptyState
            title="No alerts"
            description="No risk triggers are currently active."
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Severity</TH>
                <TH>Trigger</TH>
                <TH>Message</TH>
                <TH align="right">Exposure</TH>
                <TH>Source</TH>
                <TH>Status</TH>
                <TH>Created</TH>
                <TH>Links</TH>
              </TR>
            </THead>
            <TBody>
              {items.map((a) => (
                <TR key={a.id}>
                  <TD>
                    <Badge tone={severityTone(a.severity)}>
                      {a.severity}
                    </Badge>
                  </TD>
                  <TD className="text-slate-300">{a.trigger}</TD>
                  <TD className="max-w-[320px] whitespace-normal text-slate-200">
                    {a.message}
                  </TD>
                  <TD align="right">
                    {a.exposure != null ? fmtCurrency(a.exposure) : "—"}
                  </TD>
                  <TD className="text-xs text-slate-400">{a.source}</TD>
                  <TD>
                    <Badge tone={severityTone(a.status)}>{a.status}</Badge>
                  </TD>
                  <TD className="text-xs text-slate-400">
                    {fmtDateTime(a.created_at)}
                  </TD>
                  <TD className="space-x-2 text-xs">
                    {a.instrument_id ? (
                      <Link
                        href={`/instruments/${a.instrument_id}`}
                        className="text-accent hover:underline"
                      >
                        Instrument
                      </Link>
                    ) : null}
                    {a.portfolio_id ? (
                      <Link
                        href={`/portfolios/${a.portfolio_id}`}
                        className="text-accent hover:underline"
                      >
                        Portfolio
                      </Link>
                    ) : null}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
