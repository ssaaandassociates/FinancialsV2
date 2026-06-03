import { SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...p }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-10 w-full rounded-lg border border-line bg-white px-3 text-sm text-ink outline-none transition-colors focus:border-navy focus:ring-2 focus:ring-navy/10",
        className
      )}
      {...p}
    >
      {children}
    </select>
  )
);
Select.displayName = "Select";
