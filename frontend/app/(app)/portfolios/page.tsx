"use client";

import { useState } from "react";
import Link from "next/link";
import * as api from "@/services/api";
import { ApiError } from "@/services/api";
import { useAsync } from "@/lib/useAsync";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/States";
import { fmtCurrency } from "@/lib/format";

export default function PortfoliosPage() {
  const { data, loading, error, reload } = useAsync(
    () => api.listPortfolios(),
    []
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const items = data?.items ?? [];

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setFormError(null);
    try {
      await api.createPortfolio(name.trim(), description.trim() || undefined);
      setName("");
      setDescription("");
      reload();
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : "Failed to create portfolio"
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Portfolios"
        description="Manage your simulated fixed-income portfolios."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader title="Your portfolios" />
            {loading ? (
              <LoadingState label="Loading portfolios…" />
            ) : error ? (
              <ErrorState message={error} onRetry={reload} />
            ) : !items.length ? (
              <EmptyState
                title="No portfolios yet"
                description="Create your first portfolio using the form."
              />
            ) : (
              <div className="divide-y divide-navy-700">
                {items.map((p) => (
                  <Link
                    key={p.id}
                    href={`/portfolios/${p.id}`}
                    className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-navy-800"
                  >
                    <div>
                      <div className="text-sm font-medium text-slate-100">
                        {p.name}
                      </div>
                      {p.description ? (
                        <div className="text-xs text-slate-500">
                          {p.description}
                        </div>
                      ) : null}
                    </div>
                    <div className="text-right">
                      {p.total_value != null ? (
                        <div className="tabular text-sm text-slate-200">
                          {fmtCurrency(p.total_value)}
                        </div>
                      ) : null}
                      {p.holdings_count != null ? (
                        <div className="text-xs text-slate-500">
                          {p.holdings_count} holdings
                        </div>
                      ) : null}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader title="Create portfolio" />
            <CardBody>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Core Income"
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Optional"
                  />
                </div>
                {formError ? (
                  <div className="rounded-md border border-negative/30 bg-negative/10 px-3 py-2 text-xs text-negative">
                    {formError}
                  </div>
                ) : null}
                <Button type="submit" className="w-full" disabled={creating}>
                  {creating ? "Creating…" : "Create portfolio"}
                </Button>
              </form>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
