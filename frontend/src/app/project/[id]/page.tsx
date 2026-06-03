"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { TopNav } from "@/components/top-nav";
import { Card, CardBody } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Upload, Edit3, Eye, FileText, ChevronRight, Layers } from "lucide-react";
import { mappingApi, type MappingSummary } from "@/lib/mapping-api";
import { auditApi } from "@/lib/project-api";

export default function ProjectPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { session, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<MappingSummary | null>(null);
  const [auditCount, setAuditCount] = useState<number | null>(null);

  useEffect(() => { if (!authLoading && !session) router.replace("/login"); }, [session, authLoading, router]);

  useEffect(() => {
    if (!session || !projectId) return;
    mappingApi.summary(projectId).then(setSummary).catch(() => setSummary({ total: 0, mapped: 0, unmapped: 0, custom_coa: 0 }));
    auditApi.list(projectId).then((rows) => setAuditCount(rows.length)).catch(() => setAuditCount(0));
  }, [session, projectId]);

  if (authLoading || !session) return null;

  const steps = [
    {
      id: "upload", title: "Upload & Map", icon: Upload,
      desc: "Upload TB, auto-map ledgers to CoA codes, fix the rest manually.",
      href: `/project/${projectId}/upload`,
      done: summary && summary.total > 0 && summary.unmapped === 0,
      stat: summary ? `${summary.mapped}/${summary.total} mapped` : "—",
    },
    {
      id: "audit", title: "Audit entries", icon: Edit3,
      desc: "Add adjusting journal entries to arrive at final balances.",
      href: `/project/${projectId}/audit`,
      done: false,
      stat: auditCount != null ? `${auditCount} entr${auditCount === 1 ? "y" : "ies"}` : "—",
    },
    {
      id: "data", title: "Enrich data", icon: Layers,
      desc: "Ageing, ratios, related parties, closing stock, PPE, signing block.",
      href: `/project/${projectId}/data`,
      done: false, stat: "5 sections",
    },
    {
      id: "preview", title: "Preview & Export", icon: Eye,
      desc: "Review the full Schedule III output and export the workbook.",
      href: `/project/${projectId}/preview`,
      done: false, stat: "BS / P&L / Notes / CF / Ratios / EPS",
    },
  ];

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Link href="/dashboard" className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
          <ArrowLeft className="h-4 w-4" /> All clients
        </Link>
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold text-navy">Project workspace</h1>
            <p className="mt-1 text-sm text-muted">Project #{projectId} · follow the workflow below.</p>
          </div>
        </div>

        <div className="space-y-2">
          {steps.map((s) => (
            <Link key={s.id} href={s.href}>
              <Card className="transition-shadow hover:shadow-md">
                <CardBody className="flex items-center gap-4">
                  <div className="rounded-lg bg-navy-pale p-3 text-navy"><s.icon className="h-5 w-5" /></div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="font-medium text-navy">{s.title}</div>
                      {s.done && <Badge tone="ok">Complete</Badge>}
                    </div>
                    <div className="mt-0.5 text-sm text-muted">{s.desc}</div>
                  </div>
                  <div className="text-sm text-muted">{s.stat}</div>
                  <ChevronRight className="h-4 w-4 text-muted" />
                </CardBody>
              </Card>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
