import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

type Tone = "neutral" | "ok" | "danger" | "gold" | "navy";
const tones: Record<Tone, string> = {
  neutral: "bg-surface text-muted border-line",
  ok: "bg-okpale text-ok border-ok/20",
  danger: "bg-dangerpale text-danger border-danger/20",
  gold: "bg-gold-light text-gold border-gold/30",
  navy: "bg-navy-pale text-navy border-navy/15",
};

export function Badge({ tone = "neutral", className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}
