"use client";
import { ReactNode } from "react";
import Link from "next/link";
import { TopNav } from "@/components/top-nav";
import { ArrowLeft } from "lucide-react";

export function ProjectPageShell({
  projectId,
  title,
  subtitle,
  actions,
  children,
}: {
  projectId: number;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen pb-12">
      <TopNav />
      <div className="sticky top-16 z-20 border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-2.5">
          <div className="flex items-center gap-3 text-sm">
            <Link href={`/project/${projectId}`} className="inline-flex items-center gap-1 text-muted hover:text-ink">
              <ArrowLeft className="h-4 w-4" /> Project
            </Link>
            <span className="text-muted">·</span>
            <span className="font-medium text-navy">{title}</span>
          </div>
          {actions}
        </div>
      </div>
      <main className="mx-auto max-w-7xl px-6 py-6">
        {subtitle && <p className="mb-4 text-sm text-muted">{subtitle}</p>}
        {children}
      </main>
    </div>
  );
}
