"use client";

import { useState } from "react";
import Link from "next/link";
import * as api from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input, Select } from "@/components/ui/Input";
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
  fmtDate,
  fmtNumber,
  fmtPercent,
  liquidityTone,
  ratingTone,
} from "@/lib/format";

const CATEGORIES = [
  "",
  "G-Sec",
  "T-Bill",
  "SDL",
  "PSU",
  "Corporate",
  "Municipal",
  "Covered",
];

const PAGE_SIZE = 25;

export default function InstrumentsPage() {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(1);

  const { data, loading, error, reload } = useAsync(
    () =>
      api.listInstruments({
        search: query || undefined,
        category: category || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    [query, category, page]
  );

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  function applySearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setQuery(search);
  }

  return (
    <div>
      <PageHeader
        title="Instruments"
        description="Browse the simulated fixed-income universe."
      />

      <Card className="mb-4 p-3">
        <div className="flex flex-wrap items-end gap-3">
          <form onSubmit={applySearch} className="flex-1">
            <div className="flex gap-2">
              <Input
                placeholder="Search by name, ISIN or issuer…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <Button type="submit" variant="secondary">
                Search
              </Button>
            </div>
          </form>
          <div className="w-48">
            <Select
              value={category}
              onChange={(e) => {
                setPage(1);
                setCategory(e.target.value);
              }}
              aria-label="Filter by category"
            >
              {CATEGORIES.map((c) => (
                <option key={c || "all"} value={c}>
                  {c || "All categories"}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      <Card>
        {loading ? (
          <LoadingState label="Loading instruments…" />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : !items.length ? (
          <EmptyState
            title="No instruments found"
            description="Try adjusting your search or category filter."
          />
        ) : (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Name</TH>
                  <TH>ISIN</TH>
                  <TH>Category</TH>
                  <TH>Issuer</TH>
                  <TH align="right">Coupon</TH>
                  <TH>Maturity</TH>
                  <TH align="right">Price</TH>
                  <TH align="right">YTM</TH>
                  <TH align="right">Mod. Dur.</TH>
                  <TH>Rating</TH>
                  <TH>Liquidity</TH>
                </TR>
              </THead>
              <TBody>
                {items.map((inst) => (
                  <TR key={inst.id}>
                    <TD>
                      <Link
                        href={`/instruments/${inst.id}`}
                        className="font-medium text-accent hover:underline"
                      >
                        {inst.name}
                      </Link>
                    </TD>
                    <TD className="tabular text-xs text-slate-400">
                      {inst.isin}
                    </TD>
                    <TD>
                      <Badge tone={inst.is_government ? "accent" : "neutral"}>
                        {inst.category}
                      </Badge>
                    </TD>
                    <TD className="max-w-[180px] truncate">
                      {inst.issuer_name}
                    </TD>
                    <TD align="right">{fmtPercent(inst.coupon_rate)}</TD>
                    <TD>{fmtDate(inst.maturity_date)}</TD>
                    <TD align="right">{fmtNumber(inst.clean_price)}</TD>
                    <TD align="right">{fmtPercent(inst.ytm)}</TD>
                    <TD align="right">
                      {fmtNumber(inst.modified_duration)}
                    </TD>
                    <TD>
                      {inst.rating ? (
                        <Badge tone={ratingTone(inst.rating)}>
                          {inst.rating}
                        </Badge>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </TD>
                    <TD>
                      {inst.liquidity_class ? (
                        <Badge tone={liquidityTone(inst.liquidity_class)}>
                          {inst.liquidity_class}
                        </Badge>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>

            <div className="flex items-center justify-between border-t border-navy-700 px-4 py-3 text-xs text-slate-400">
              <span>
                {total.toLocaleString()} instruments · page {page} of{" "}
                {totalPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
