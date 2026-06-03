"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Empty } from "@/components/ui/empty";
import { Clock } from "lucide-react";
import { ageingApi, type AgeingMatrix } from "@/lib/project-api";

export default function AgeingPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [tr, setTr] = useState<AgeingMatrix | null>(null);
  const [tp, setTp] = useState<AgeingMatrix | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!session) return;
    Promise.all([ageingApi.tr(pid).catch(() => null), ageingApi.tp(pid).catch(() => null)])
      .then(([t1, t2]) => { setTr(t1); setTp(t2); })
      .catch((e) => setErr(e?.message || "Failed to load"));
  }, [session, pid]);

  if (loading || !session) return null;

  const Matrix = ({ title, data, year }: { title: string; data: AgeingMatrix | null; year: "cy" | "py" }) => {
    if (!data) return <Card><CardBody><Empty icon={<Clock className="h-6 w-6" />} title={`No ${title} data`} hint="Map TB ledgers to BS-AS-02-03 (TR) or BS-EL-04-02 (TP) leaf codes." /></CardBody></Card>;
    const matrix = data[year] || { rows: {} };
    const buckets = Array.isArray(data.buckets) ? data.buckets : [];
    const categories = Array.isArray(data.categories) ? data.categories : Object.keys(matrix.rows || {});
    return (
      <Card>
        <CardHeader><h3 className="font-medium text-navy">{title} — {year === "cy" ? "Current year" : "Previous year"}</h3></CardHeader>
        <CardBody className="!p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                <th className="px-4 py-3">Category</th>
                {buckets.map((b) => <th key={b} className="px-4 py-3 text-right">{b}</th>)}
                <th className="px-4 py-3 text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => {
                const row = matrix.rows[cat] || {};
                const total = buckets.reduce((s, b) => s + (row[b] || 0), 0);
                return (
                  <tr key={cat} className="border-b border-line last:border-0">
                    <td className="px-4 py-3 font-medium text-ink">{cat}</td>
                    {buckets.map((b) => (
                      <td key={b} className="px-4 py-3 text-right font-mono tabular-nums">
                        {row[b] ? row[b].toLocaleString("en-IN") : "—"}
                      </td>
                    ))}
                    <td className="px-4 py-3 text-right font-mono tabular-nums font-semibold">
                      {total ? total.toLocaleString("en-IN") : "—"}
                    </td>
                  </tr>
                );
              })}
              <tr className="bg-navy-pale/40">
                <td className="px-4 py-3 font-semibold text-navy">Grand total</td>
                <td colSpan={buckets.length} />
                <td className="px-4 py-3 text-right font-mono tabular-nums font-semibold text-navy">
                  {matrix.grand_total?.toLocaleString("en-IN") || "—"}
                </td>
              </tr>
            </tbody>
          </table>
        </CardBody>
      </Card>
    );
  };

  return (
    <ProjectPageShell projectId={pid} title="TR / TP Ageing" subtitle="Auto-derived from your trial balance mappings — no separate upload needed.">
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}
      <div className="space-y-4">
        <h2 className="font-display text-xl font-semibold text-navy">Trade Receivables</h2>
        <Matrix title="TR Ageing" data={tr} year="cy" />
        <Matrix title="TR Ageing" data={tr} year="py" />
        <h2 className="mt-6 font-display text-xl font-semibold text-navy">Trade Payables</h2>
        <Matrix title="TP Ageing" data={tp} year="cy" />
        <Matrix title="TP Ageing" data={tp} year="py" />
      </div>
    </ProjectPageShell>
  );
}
