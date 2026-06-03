"use client";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Tab { id: string; label: string; count?: number; }

export function Tabs({
  tabs, value, onChange,
}: { tabs: Tab[]; value: string; onChange: (id: string) => void }) {
  return (
    <div className="border-b border-line">
      <div className="flex gap-1 overflow-x-auto">
        {tabs.map((t) => {
          const active = t.id === value;
          return (
            <button
              key={t.id}
              onClick={() => onChange(t.id)}
              className={cn(
                "relative whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "border-gold text-navy"
                  : "border-transparent text-muted hover:text-ink"
              )}
            >
              {t.label}
              {typeof t.count === "number" && (
                <span className={cn("ml-1.5 rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                  active ? "bg-gold/15 text-gold" : "bg-surface text-muted")}>
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function TabPanel({ when, current, children }: { when: string; current: string; children: ReactNode }) {
  if (when !== current) return null;
  return <div className="rise pt-6">{children}</div>;
}
