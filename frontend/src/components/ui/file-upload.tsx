"use client";
import { useRef, useState } from "react";
import { Upload, FileSpreadsheet, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileDropProps {
  onFile: (f: File) => void;
  accept?: string;
  hint?: string;
  disabled?: boolean;
  compact?: boolean;
}

export function FileDrop({ onFile, accept = ".xlsx,.xls,.csv", hint, disabled, compact }: FileDropProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);

  function take(f: File) {
    setSelected(f);
    onFile(f);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault(); setDragOver(false);
    if (disabled) return;
    const f = e.dataTransfer.files[0];
    if (f) take(f);
  }

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => e.target.files?.[0] && take(e.target.files[0])}
          disabled={disabled}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface disabled:opacity-50"
        >
          <Upload className="h-4 w-4" /> Choose file
        </button>
        {selected && (
          <span className="flex items-center gap-1.5 text-sm text-muted">
            <FileSpreadsheet className="h-4 w-4" /> {selected.name}
            <button onClick={() => { setSelected(null); if (inputRef.current) inputRef.current.value = ""; }} className="ml-1 text-muted hover:text-ink"><X className="h-3 w-3" /></button>
          </span>
        )}
        {hint && !selected && <span className="text-xs text-muted">{hint}</span>}
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={cn(
        "rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors cursor-pointer",
        dragOver ? "border-gold bg-gold-light/30" : "border-line bg-white hover:border-navy/30 hover:bg-surface",
        disabled && "opacity-50 pointer-events-none"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => e.target.files?.[0] && take(e.target.files[0])}
      />
      {selected ? (
        <div className="flex items-center justify-center gap-2 text-ink">
          <FileSpreadsheet className="h-5 w-5 text-gold" />
          <span className="font-medium">{selected.name}</span>
          <button
            onClick={(e) => { e.stopPropagation(); setSelected(null); if (inputRef.current) inputRef.current.value = ""; }}
            className="ml-2 text-muted hover:text-ink"
          ><X className="h-4 w-4" /></button>
        </div>
      ) : (
        <>
          <Upload className="mx-auto h-7 w-7 text-muted" />
          <div className="mt-2 text-sm font-medium text-ink">Drop file here or click to browse</div>
          <div className="mt-1 text-xs text-muted">{hint || `Accepts ${accept}`}</div>
        </>
      )}
    </div>
  );
}
