"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Sidebar } from "./Sidebar";
import { SimulatedBanner } from "./SimulatedBanner";
import { LoadingState } from "./ui/States";

// Wraps all authenticated pages: enforces the auth guard, renders the
// persistent sidebar and the global SIMULATED banner.
export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-navy-900">
        <LoadingState label="Starting RiskLens…" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-navy-900">
        <LoadingState label="Redirecting to sign in…" />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-navy-900">
      <SimulatedBanner />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-6 py-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
