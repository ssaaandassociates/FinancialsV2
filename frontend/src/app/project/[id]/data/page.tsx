"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody } from "@/components/ui/card";
import { Clock, BarChart3, Users, Package, FileSignature, ChevronRight } from "lucide-react";

export default function DataHubPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  if (loading || !session) return null;

  const sections = [
    { id: "ageing",  title: "TR / TP Ageing",        desc: "Auto-derived from your TB mappings (BS-AS-02-03 and BS-EL-04-02 leaves).", icon: Clock },
    { id: "ratios",  title: "Ratios & EPS",          desc: "Enter PY-1 averages, compute 11 mandatory ratios with variance flagging.", icon: BarChart3 },
    { id: "related-parties", title: "Related Parties", desc: "KMP, holding/subsidiary/associate parties + transactions.", icon: Users },
    { id: "stock-ppe", title: "Closing stock & PPE", desc: "Closing stock split + PPE schedule (gross/depreciation, CY + PY).", icon: Package },
    { id: "signing", title: "Signing & Disclosures", desc: "Signing block, additional Sch III disclosures, accounting policies.", icon: FileSignature },
  ];

  return (
    <ProjectPageShell projectId={pid} title="Enrich data" subtitle="Fill these to complete the financial statements.">
      <div className="space-y-2">
        {sections.map((s) => (
          <Link key={s.id} href={`/project/${pid}/data/${s.id}`}>
            <Card className="transition-shadow hover:shadow-md">
              <CardBody className="flex items-center gap-4">
                <div className="rounded-lg bg-navy-pale p-3 text-navy"><s.icon className="h-5 w-5" /></div>
                <div className="flex-1">
                  <div className="font-medium text-navy">{s.title}</div>
                  <div className="mt-0.5 text-sm text-muted">{s.desc}</div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted" />
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </ProjectPageShell>
  );
}
