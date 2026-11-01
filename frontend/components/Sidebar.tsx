"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useAuth } from "@/context/AuthContext";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  match?: (path: string) => boolean;
}

function Icon({ d }: { d: string }) {
  return (
    <svg
      className="h-4 w-4 shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={d} />
    </svg>
  );
}

const NAV: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    icon: <Icon d="M3 13h8V3H3v10Zm0 8h8v-6H3v6Zm10 0h8V11h-8v10Zm0-18v6h8V3h-8Z" />,
    match: (p) => p === "/",
  },
  {
    href: "/instruments",
    label: "Instruments",
    icon: <Icon d="M4 19V5m4 14V9m4 10V7m4 12v-8m4 8V3" />,
    match: (p) => p.startsWith("/instruments"),
  },
  {
    href: "/portfolio-builder",
    label: "Portfolio Builder",
    icon: <Icon d="M12 20v-6m0 0V4m0 10 4-4m-4 4-4-4M4 20h16" />,
    match: (p) => p.startsWith("/portfolio-builder"),
  },
  {
    href: "/portfolios",
    label: "Portfolios",
    icon: <Icon d="M3 7h18M3 12h18M3 17h18" />,
    match: (p) => p.startsWith("/portfolios"),
  },
  {
    href: "/alerts",
    label: "Alerts",
    icon: <Icon d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" />,
    match: (p) => p.startsWith("/alerts"),
  },
  {
    href: "/reports",
    label: "Reports",
    icon: <Icon d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Zm0 0v6h6M9 13h6M9 17h6" />,
    match: (p) => p.startsWith("/reports"),
  },
];

export function Sidebar() {
  const pathname = usePathname() || "/";
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-navy-700 bg-navy-950">
      <div className="flex items-center gap-2 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-accent text-sm font-bold text-white">
          R
        </div>
        <div>
          <div className="text-sm font-semibold text-slate-100">RiskLens</div>
          <div className="text-[10px] uppercase tracking-wider text-slate-500">
            Fixed-Income Analytics
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map((item) => {
          const active = item.match
            ? item.match(pathname)
            : pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-navy-800 text-slate-100"
                  : "text-slate-400 hover:bg-navy-850 hover:text-slate-200"
              )}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-navy-700 px-3 py-3">
        <div className="mb-2 px-2">
          <div className="truncate text-xs font-medium text-slate-200">
            {user?.full_name || user?.email || "—"}
          </div>
          <div className="truncate text-[10px] text-slate-500">
            {user?.email}
          </div>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-400 transition-colors hover:bg-navy-850 hover:text-slate-200"
        >
          <Icon d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
