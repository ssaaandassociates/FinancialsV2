"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, Check, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ComboOption {
  value: string;
  label: string;       // primary text shown
  sublabel?: string;   // secondary text (e.g. particulars next to code)
  disabled?: boolean;
}

interface ComboboxProps {
  value: string;
  onChange: (v: string) => void;
  options: ComboOption[];
  placeholder?: string;
  emptyText?: string;
  disabled?: boolean;
  size?: "sm" | "md";
  className?: string;
  /** Show the SELECTED label as `value · label`; otherwise just label */
  showValueInTrigger?: boolean;
}

export function Combobox({
  value, onChange, options, placeholder = "Select…", emptyText = "No matches",
  disabled, size = "md", className, showValueInTrigger = true,
}: ComboboxProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selected = options.find((o) => o.value === value);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (o) =>
        o.value.toLowerCase().includes(q) ||
        o.label.toLowerCase().includes(q) ||
        (o.sublabel && o.sublabel.toLowerCase().includes(q))
    );
  }, [options, query]);

  // Click outside to close
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  // Focus search input when opened
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  // Reset highlight when filter changes
  useEffect(() => { setHighlight(0); }, [query]);

  function pick(opt: ComboOption) {
    if (opt.disabled) return;
    onChange(opt.value);
    setOpen(false);
    setQuery("");
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") { e.preventDefault(); setOpen(false); setQuery(""); return; }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, filtered.length - 1));
      scrollToHighlight(highlight + 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
      scrollToHighlight(highlight - 1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[highlight]) pick(filtered[highlight]);
    }
  }

  function scrollToHighlight(i: number) {
    const ul = listRef.current;
    if (!ul) return;
    const el = ul.children[i] as HTMLElement | undefined;
    if (el) el.scrollIntoView({ block: "nearest" });
  }

  const triggerSize =
    size === "sm" ? "h-8 px-2 text-xs" : "h-9 px-2.5 text-sm";

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center justify-between gap-2 rounded-md border border-line bg-white text-left text-ink outline-none transition-colors hover:border-navy/30 focus:border-navy focus:ring-2 focus:ring-navy/10 disabled:cursor-not-allowed disabled:bg-surface disabled:text-muted",
          triggerSize
        )}
      >
        <span className={cn("truncate", !selected && "text-muted")}>
          {selected
            ? showValueInTrigger
              ? <><span className="font-mono">{selected.value}</span><span className="ml-2 text-muted">{selected.label}</span></>
              : selected.label
            : placeholder}
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute z-30 mt-1 w-full min-w-[280px] overflow-hidden rounded-lg border border-line bg-white shadow-lg">
          <div className="flex items-center gap-2 border-b border-line px-2.5 py-2">
            <Search className="h-3.5 w-3.5 text-muted" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKey}
              placeholder="Type to filter…"
              className="h-6 w-full bg-transparent text-xs text-ink outline-none placeholder:text-muted"
            />
            {query && (
              <button onClick={() => setQuery("")} className="text-xs text-muted hover:text-ink">×</button>
            )}
          </div>
          {filtered.length === 0 ? (
            <div className="px-3 py-4 text-center text-xs text-muted">{emptyText}</div>
          ) : (
            <ul ref={listRef} className="max-h-64 overflow-y-auto py-1">
              {filtered.map((o, i) => (
                <li
                  key={o.value}
                  onClick={() => pick(o)}
                  onMouseEnter={() => setHighlight(i)}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 px-2.5 py-1.5 text-xs",
                    i === highlight && "bg-surface",
                    o.disabled && "opacity-50 cursor-not-allowed",
                    o.value === value && "font-medium"
                  )}
                >
                  <Check className={cn("h-3 w-3 shrink-0", o.value === value ? "text-gold" : "invisible")} />
                  <span className="font-mono text-navy">{o.value}</span>
                  <span className="truncate text-ink/80">{o.label}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
