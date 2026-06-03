"use client";
import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, id, ...p }, ref) => {
    const inputId = id || `cb-${Math.random().toString(36).slice(2, 9)}`;
    return (
      <label htmlFor={inputId} className="inline-flex cursor-pointer items-center gap-2 text-sm text-ink">
        <span className="relative">
          <input
            id={inputId}
            ref={ref}
            type="checkbox"
            className={cn(
              "peer h-4 w-4 cursor-pointer appearance-none rounded border border-line bg-white checked:border-navy checked:bg-navy focus:ring-2 focus:ring-navy/20",
              className
            )}
            {...p}
          />
          <Check className="pointer-events-none absolute left-0 top-0 h-4 w-4 text-white opacity-0 peer-checked:opacity-100" />
        </span>
        {label && <span>{label}</span>}
      </label>
    );
  }
);
Checkbox.displayName = "Checkbox";
