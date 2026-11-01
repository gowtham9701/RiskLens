"use client";

import { useState } from "react";
import * as api from "@/services/api";
import { ApiError } from "@/services/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table";
import { ErrorState, LoadingState } from "@/components/ui/States";
import { StatCard } from "@/components/ui/StatCard";
import {
  fmtCurrency,
  fmtNumber,
  fmtPercent,
  liquidityTone,
  ratingTone,
} from "@/lib/format";
import type {
  BuilderObjective,
  BuilderResult,
} from "@/lib/types";

const OBJECTIVES: { value: BuilderObjective; label: string }[] = [
  { value: "max_yield", label: "Maximise yield" },
  { value: "max_income", label: "Maximise income" },
  { value: "min_duration", label: "Minimise duration" },
  { value: "max_liquidity", label: "Maximise liquidity" },
];

const UNIVERSE = [
  "G-Sec",
  "T-Bill",
  "SDL",
  "PSU",
  "Corporate",
  "Municipal",
  "Covered",
];

interface FormState {
  amount: number;
  objective: BuilderObjective;
  max_issuer_weight: number;
  max_sector_weight: number;
  min_government_weight: number;
  max_low_rated_weight: number;
  min_liquidity_weight: number;
  max_duration: number;
  max_maturity_years: number;
  max_weight_per_instrument: number;
  min_instruments: number;
}

const DEFAULTS: FormState = {
  amount: 1000000,
  objective: "max_yield",
  max_issuer_weight: 20,
  max_sector_weight: 40,
  min_government_weight: 20,
  max_low_rated_weight: 15,
  min_liquidity_weight: 50,
  max_duration: 7,
  max_maturity_years: 15,
  max_weight_per_instrument: 10,
  min_instruments: 5,
};

function PercentSlider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <Label className="mb-0">{label}</Label>
        <span className="tabular text-xs text-slate-300">{value}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-accent"
      />
    </div>
  );
}

export default function PortfolioBuilderPage() {
  const [form, setForm] = useState<FormState>(DEFAULTS);
  const [universe, setUniverse] = useState<string[]>([...UNIVERSE]);
  const [result, setResult] = useState<BuilderResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleUniverse(cat: string) {
    setUniverse((u) =>
      u.includes(cat) ? u.filter((c) => c !== cat) : [...u, cat]
    );
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.generatePortfolio({
        amount: form.amount,
        objective: form.objective,
        constraints: {
          max_issuer_weight: form.max_issuer_weight / 100,
          max_sector_weight: form.max_sector_weight / 100,
          min_government_weight: form.min_government_weight / 100,
          max_low_rated_weight: form.max_low_rated_weight / 100,
          min_liquidity_weight: form.min_liquidity_weight / 100,
          max_duration: form.max_duration,
          max_maturity_years: form.max_maturity_years,
          max_weight_per_instrument: form.max_weight_per_instrument / 100,
          min_instruments: form.min_instruments,
        },
        universe,
      });
      setResult(res);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to generate portfolio"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Portfolio Builder"
        description="Generate a simulated allocation from your objective and constraints."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Parameters" />
          <CardBody>
            <form onSubmit={handleGenerate} className="space-y-5">
              <div>
                <Label htmlFor="amount">Investment amount</Label>
                <Input
                  id="amount"
                  type="number"
                  min={0}
                  step={10000}
                  value={form.amount}
                  onChange={(e) => update("amount", Number(e.target.value))}
                />
              </div>

              <div>
                <Label htmlFor="objective">Objective</Label>
                <Select
                  id="objective"
                  value={form.objective}
                  onChange={(e) =>
                    update("objective", e.target.value as BuilderObjective)
                  }
                >
                  {OBJECTIVES.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-3">
                <PercentSlider
                  label="Max issuer weight"
                  value={form.max_issuer_weight}
                  onChange={(v) => update("max_issuer_weight", v)}
                />
                <PercentSlider
                  label="Max sector weight"
                  value={form.max_sector_weight}
                  onChange={(v) => update("max_sector_weight", v)}
                />
                <PercentSlider
                  label="Min government weight"
                  value={form.min_government_weight}
                  onChange={(v) => update("min_government_weight", v)}
                />
                <PercentSlider
                  label="Max low-rated weight"
                  value={form.max_low_rated_weight}
                  onChange={(v) => update("max_low_rated_weight", v)}
                />
                <PercentSlider
                  label="Min liquidity weight"
                  value={form.min_liquidity_weight}
                  onChange={(v) => update("min_liquidity_weight", v)}
                />
                <PercentSlider
                  label="Max weight / instrument"
                  value={form.max_weight_per_instrument}
                  onChange={(v) => update("max_weight_per_instrument", v)}
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <Label htmlFor="max_duration">Max dur.</Label>
                  <Input
                    id="max_duration"
                    type="number"
                    min={0}
                    step={0.5}
                    value={form.max_duration}
                    onChange={(e) =>
                      update("max_duration", Number(e.target.value))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="max_maturity_years">Max mat.</Label>
                  <Input
                    id="max_maturity_years"
                    type="number"
                    min={0}
                    step={1}
                    value={form.max_maturity_years}
                    onChange={(e) =>
                      update("max_maturity_years", Number(e.target.value))
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="min_instruments">Min inst.</Label>
                  <Input
                    id="min_instruments"
                    type="number"
                    min={1}
                    step={1}
                    value={form.min_instruments}
                    onChange={(e) =>
                      update("min_instruments", Number(e.target.value))
                    }
                  />
                </div>
              </div>

              <div>
                <Label>Universe</Label>
                <div className="grid grid-cols-2 gap-2">
                  {UNIVERSE.map((cat) => (
                    <label
                      key={cat}
                      className="flex items-center gap-2 rounded-md border border-navy-600 bg-navy-900 px-2.5 py-1.5 text-sm text-slate-200"
                    >
                      <input
                        type="checkbox"
                        checked={universe.includes(cat)}
                        onChange={() => toggleUniverse(cat)}
                        className="accent-accent"
                      />
                      {cat}
                    </label>
                  ))}
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading || universe.length === 0}
              >
                {loading ? "Generating…" : "Generate portfolio"}
              </Button>
            </form>
          </CardBody>
        </Card>

        <div className="lg:col-span-2">
          {loading ? (
            <Card>
              <LoadingState label="Optimising allocation…" />
            </Card>
          ) : error ? (
            <ErrorState message={error} />
          ) : result ? (
            <BuilderResultView result={result} />
          ) : (
            <Card>
              <CardBody>
                <p className="py-10 text-center text-sm text-slate-400">
                  Configure your parameters and generate a simulated
                  portfolio to see allocations, expected yield and duration.
                </p>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function BuilderResultView({ result }: { result: BuilderResult }) {
  return (
    <div className="space-y-4">
      {!result.feasible ? (
        <Card className="border-negative/40 bg-negative/5">
          <CardHeader title="Infeasible configuration" />
          <CardBody>
            <p className="mb-3 text-sm text-slate-300">
              No allocation satisfies all constraints. Relax one or more of
              the following:
            </p>
            {result.infeasible_reasons.length ? (
              <ul className="space-y-1.5">
                {result.infeasible_reasons.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-slate-200"
                  >
                    <span className="mt-0.5 text-negative">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">
                No specific reasons were provided.
              </p>
            )}
          </CardBody>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard
              label="Objective"
              value={
                <span className="text-base capitalize">
                  {result.objective.replace(/_/g, " ")}
                </span>
              }
            />
            <StatCard
              label="Expected Yield"
              value={fmtPercent(result.expected_yield)}
              tone="positive"
            />
            <StatCard
              label="Expected Duration"
              value={fmtNumber(result.expected_duration, 2)}
              sub="years"
            />
          </div>

          <Card>
            <CardHeader
              title="Allocations"
              subtitle={`${result.allocations.length} instruments`}
            />
            <Table>
              <THead>
                <TR>
                  <TH>Instrument</TH>
                  <TH>Category</TH>
                  <TH align="right">Weight</TH>
                  <TH align="right">Amount</TH>
                  <TH align="right">YTM</TH>
                  <TH align="right">Dur.</TH>
                  <TH>Rating</TH>
                  <TH>Liquidity</TH>
                </TR>
              </THead>
              <TBody>
                {result.allocations.map((a) => (
                  <TR key={a.instrument_id}>
                    <TD>
                      <div className="font-medium text-slate-100">
                        {a.name}
                      </div>
                      <div className="text-xs text-slate-500">
                        {a.issuer}
                      </div>
                    </TD>
                    <TD>
                      <Badge tone="neutral">{a.category}</Badge>
                    </TD>
                    <TD align="right">{fmtPercent(a.weight)}</TD>
                    <TD align="right">{fmtCurrency(a.amount)}</TD>
                    <TD align="right">{fmtPercent(a.ytm)}</TD>
                    <TD align="right">{fmtNumber(a.modified_duration)}</TD>
                    <TD>
                      {a.rating ? (
                        <Badge tone={ratingTone(a.rating)}>{a.rating}</Badge>
                      ) : (
                        "—"
                      )}
                    </TD>
                    <TD>
                      {a.liquidity_class ? (
                        <Badge tone={liquidityTone(a.liquidity_class)}>
                          {a.liquidity_class}
                        </Badge>
                      ) : (
                        "—"
                      )}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </Card>
        </>
      )}

      {result.methodology ? (
        <Card>
          <CardHeader title="Methodology" />
          <CardBody>
            <p className="text-xs leading-relaxed text-slate-400">
              {result.methodology}
            </p>
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}
