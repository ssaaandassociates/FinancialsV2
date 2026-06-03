"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, AlertTriangle, Save } from "lucide-react";
import { ratiosApi, type RatioPY1Row, type ComputedRatio } from "@/lib/project-api";

export default function RatiosPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [py1, setPy1] = useState<RatioPY1Row[]>([]);
  const [computed, setComputed] = useState<ComputedRatio[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function reload() {
    setErr("");
    try {
      const [p, c] = await Promise.all([ratiosApi.py1Get(pid), ratiosApi.compute(pid)]);
      setPy1(Array.isArray(p) ? p : []); setComputed(Array.isArray(c?.ratios) ? c.ratios : []);
    } catch (e: any) { setErr(e?.message || "Failed to load"); }
  }
  useEffect(() => { if (session) reload(); }, [session, pid]);

  async function recompute() {
    setBusy(true);
    try { await ratiosApi.py1Save({ project_id: pid, ratios: py1 }); await reload(); }
    catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  function updPy1(key: string, field: "py1_numerator" | "py1_denominator", v: number) {
    setPy1((prev) => {
      const found = prev.find((r) => r.ratio_key === key);
      if (found) return prev.map((r) => r.ratio_key === key ? { ...r, [field]: v } : r);
      return [...prev, { ratio_key: key, [field]: v } as RatioPY1Row];
    });
  }

  if (loading || !session) return null;

  const flaggedCount = computed.filter((r) => r.flagged).length;

  return (
    <ProjectPageShell projectId={pid} title="Ratios & EPS"
      actions={<Button size="sm" onClick={recompute} disabled={busy}><RefreshCw className="h-4 w-4" />{busy ? "Computing…" : "Recompute"}</Button>}>
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      <Card className="mb-4">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="font-medium text-navy">Computed ratios</h3>
            {flaggedCount > 0 && <Badge tone="danger"><AlertTriangle className="h-3 w-3 mr-1" />{flaggedCount} variance &gt; 25%</Badge>}
          </div>
        </CardHeader>
        <CardBody className="!p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Ratio</th>
                <th className="px-4 py-3">Numerator / Denominator</th>
                <th className="px-4 py-3 text-right">CY</th>
                <th className="px-4 py-3 text-right">PY</th>
                <th className="px-4 py-3 text-right">Variance %</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {computed.map((r, i) => (
                <tr key={r.key} className={`border-b border-line last:border-0 ${r.flagged ? "bg-dangerpale/40" : ""}`}>
                  <td className="px-4 py-3 text-muted">{i + 1}</td>
                  <td className="px-4 py-3 font-medium text-navy">{r.name}</td>
                  <td className="px-4 py-3 text-xs italic text-muted">{r.numerator_desc} / {r.denominator_desc}</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">{r.cy_value != null ? Number(r.cy_value).toFixed(2) : "—"}</td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums text-muted">{r.py_value != null ? Number(r.py_value).toFixed(2) : "—"}</td>
                  <td className={`px-4 py-3 text-right font-mono tabular-nums ${r.flagged ? "text-danger font-semibold" : ""}`}>{r.variance_pct != null ? `${r.variance_pct > 0 ? "+" : ""}${Number(r.variance_pct).toFixed(1)}%` : "—"}</td>
                  <td className="px-4 py-3">{r.flagged && <Badge tone="danger">▲25%</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><h3 className="font-medium text-navy">PY-1 inputs (for ratio averages)</h3></CardHeader>
        <CardBody className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {computed.map((r) => {
            const found = py1.find((x) => x.ratio_key === r.key);
            return (
              <div key={r.key} className="rounded-lg border border-line p-3">
                <div className="text-xs font-medium text-navy">{r.name}</div>
                <div className="mt-1 text-[10px] text-muted">{r.numerator_desc} / {r.denominator_desc}</div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <Input type="number" placeholder="Numerator PY-1" value={found?.py1_numerator ?? ""} onChange={(e) => updPy1(r.key, "py1_numerator", Number(e.target.value))} />
                  <Input type="number" placeholder="Denominator PY-1" value={found?.py1_denominator ?? ""} onChange={(e) => updPy1(r.key, "py1_denominator", Number(e.target.value))} />
                </div>
              </div>
            );
          })}
        </CardBody>
      </Card>
      <div className="mt-4 text-center">
        <Button onClick={recompute} disabled={busy}><Save className="h-4 w-4" />{busy ? "Saving + computing…" : "Save & recompute"}</Button>
      </div>
    </ProjectPageShell>
  );
}
