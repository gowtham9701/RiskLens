"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

export interface TabItem {
  id: string;
  label: string;
  content: React.ReactNode;
}

export function Tabs({
  items,
  initial,
}: {
  items: TabItem[];
  initial?: string;
}) {
  const [active, setActive] = useState(initial ?? items[0]?.id);
  const activeItem = items.find((i) => i.id === active) ?? items[0];
  return (
    <div>
      <div className="flex flex-wrap gap-1 border-b border-navy-700">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              active === item.id
                ? "border-accent text-slate-100"
                : "border-transparent text-slate-400 hover:text-slate-200"
            )}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="pt-4">{activeItem?.content}</div>
    </div>
  );
}
