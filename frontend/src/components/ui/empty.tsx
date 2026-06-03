import { ReactNode } from "react";

export function Empty({
  icon, title, hint, action,
}: { icon?: ReactNode; title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line py-10 text-center">
      {icon && <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center text-muted">{icon}</div>}
      <div className="font-medium text-ink">{title}</div>
      {hint && <div className="mt-1 text-sm text-muted">{hint}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
