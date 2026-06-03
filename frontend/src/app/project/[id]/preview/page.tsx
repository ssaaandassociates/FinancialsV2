"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabPanel } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Download, FileText, Check, AlertCircle, RefreshCw, ExternalLink, Edit3 } from "lucide-react";
import { generateApi, exportRoutes, type BSLine, type NoteSection, type CashFlowSection, type ComputedRatio } from "@/lib/project-api";

type TabId = "bs" | "pl" | "notes" | "cashflow" | "ratios" | "eps";

export default function PreviewPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [tab, setTab] = useState<TabId>("bs");
  const [bs, setBs] = useState<BSLine[] | null>(null);
  const [pl, setPl] = useState<BSLine[] | null>(null);
  const [notes, setNotes] = useState<NoteSection[] | null>(null);
  const [cf, setCf] = useState<CashFlowSection[] | null>(null);
  const [ratios, setRatios] = useState<ComputedRatio[] | null>(null);
  const [eps, setEps] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [validation, setValidation] = useState<any>(null);

  // Drill-down modal
  const [drillNote, setDrillNote] = useState<string | null>(null);

  async function reload() {
    if (!pid) return;
    setBusy(true); setErr("");
    try {
      const [b, p, n, c, r, v] = await Promise.all([
        generateApi.bs(pid),
        generateApi.pl(pid),
        generateApi.notes(pid),
        generateApi.cashflow(pid),
        generateApi.ratios(pid),
        generateApi.validate(pid).catch(() => null),
      ]);
      setBs(b); setPl(p); setNotes(n); setCf(c);
      setRatios(r.ratios || []); setEps(r.eps); setValidation(v);
    } catch (e: any) { setErr(e?.message || "Failed to generate"); }
    finally { setBusy(false); }
  }
  useEffect(() => { if (session) reload(); }, [session, pid]);

  if (loading || !session) return null;

  return (
    <ProjectPageShell projectId={pid} title="Preview & Export"
      actions={
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={reload} disabled={busy}><RefreshCw className="h-4 w-4" />Refresh</Button>
          <a href={exportRoutes.excel(pid)} className="inline-flex items-center gap-1.5 rounded-lg bg-navy px-3 py-1.5 text-xs font-medium text-white hover:bg-navy-light">
            <Download className="h-3.5 w-3.5" /> Excel
          </a>
          <a href={exportRoutes.pdf(pid)} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-medium hover:bg-surface">
            <Download className="h-3.5 w-3.5" /> PDF
          </a>
        </div>
      }>
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {validation && (
        <Card className="mb-4">
          <CardBody className="flex items-center gap-3 text-sm">
            {validation.balanced ? (
              <><Check className="h-4 w-4 text-ok" /><span className="text-ok">Balance sheet balances.</span></>
            ) : (
              <><AlertCircle className="h-4 w-4 text-danger" /><span className="text-danger">BS does not balance: difference ₹{(validation.diff || 0).toLocaleString("en-IN")}</span></>
            )}
            {validation.warnings?.length > 0 && (
              <span className="text-muted text-xs">· {validation.warnings.length} warning{validation.warnings.length !== 1 ? "s" : ""}</span>
            )}
          </CardBody>
        </Card>
      )}

      <Tabs value={tab} onChange={(v) => setTab(v as TabId)} tabs={[
        { id: "bs", label: "Balance Sheet" },
        { id: "pl", label: "Profit & Loss" },
        { id: "notes", label: "Notes", count: notes?.length },
        { id: "cashflow", label: "Cash Flow" },
        { id: "ratios", label: "Ratios", count: ratios?.length },
        { id: "eps", label: "EPS" },
      ]} />

      <TabPanel when="bs" current={tab}>
        <StatementCard rows={bs} onDrill={(noteRef) => setDrillNote(noteRef)} editHref={`/project/${pid}/upload`} editLabel="Mapping" />
      </TabPanel>

      <TabPanel when="pl" current={tab}>
        <StatementCard rows={pl} onDrill={(noteRef) => setDrillNote(noteRef)} editHref={`/project/${pid}/upload`} editLabel="Mapping" />
      </TabPanel>

      <TabPanel when="notes" current={tab}>
        <div className="space-y-4">
          {notes?.map((n) => (
            <Card key={n.ref}>
              <CardBody>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-display text-lg font-semibold text-navy">{n.ref}. {n.title}</h3>
                  <Link href={`/project/${pid}/data/signing`} className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink"><Edit3 className="h-3 w-3" /> Edit</Link>
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    {n.lines.map((l, i) => (
                      <tr key={i} className={`border-b border-line last:border-0 ${l.is_total ? "bg-navy-pale/30 font-semibold" : ""}`}>
                        <td className="px-2 py-2 text-ink">{l.particulars}</td>
                        <td className="px-2 py-2 text-right font-mono tabular-nums">{l.cy?.toLocaleString("en-IN") ?? "—"}</td>
                        <td className="px-2 py-2 text-right font-mono tabular-nums text-muted">{l.py?.toLocaleString("en-IN") ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardBody>
            </Card>
          ))}
        </div>
      </TabPanel>

      <TabPanel when="cashflow" current={tab}>
        <Card>
          <CardBody>
            <h3 className="font-display text-lg font-semibold text-navy mb-3">Cash flow statement (indirect)</h3>
            {cf?.map((sec, si) => (
              <div key={si} className="mb-5">
                <h4 className="font-medium text-navy mb-2">{sec.title}</h4>
                <table className="w-full text-sm">
                  <tbody>
                    {sec.lines.map((l, i) => (
                      <tr key={i} className={`border-b border-line last:border-0 ${l.is_total ? "bg-navy-pale/30 font-semibold" : ""}`}>
                        <td className="px-2 py-2 text-ink">{l.particulars}</td>
                        <td className="px-2 py-2 text-right font-mono tabular-nums">{l.cy?.toLocaleString("en-IN") ?? "—"}</td>
                        <td className="px-2 py-2 text-right font-mono tabular-nums text-muted">{l.py?.toLocaleString("en-IN") ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </CardBody>
        </Card>
      </TabPanel>

      <TabPanel when="ratios" current={tab}>
        <Card>
          <CardBody className="!p-0">
            <div className="flex items-center justify-between px-4 py-3 border-b border-line">
              <h3 className="font-medium text-navy">Schedule III ratios</h3>
              <Link href={`/project/${pid}/data/ratios`} className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink"><Edit3 className="h-3 w-3" /> Edit PY-1</Link>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Ratio</th>
                  <th className="px-4 py-3 text-right">CY</th>
                  <th className="px-4 py-3 text-right">PY</th>
                  <th className="px-4 py-3 text-right">Variance</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {ratios?.map((r) => (
                  <tr key={r.key} className={`border-b border-line last:border-0 ${r.flagged ? "bg-dangerpale/40" : ""}`}>
                    <td className="px-4 py-3 font-medium text-navy">{r.name}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{r.cy_value != null ? Number(r.cy_value).toFixed(2) : "—"}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums text-muted">{r.py_value != null ? Number(r.py_value).toFixed(2) : "—"}</td>
                    <td className={`px-4 py-3 text-right font-mono tabular-nums ${r.flagged ? "text-danger font-semibold" : ""}`}>{r.variance_pct != null ? `${Number(r.variance_pct).toFixed(1)}%` : "—"}</td>
                    <td className="px-4 py-3">{r.flagged && <Badge tone="danger">▲25%</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardBody>
        </Card>
      </TabPanel>

      <TabPanel when="eps" current={tab}>
        <Card>
          <CardBody>
            <h3 className="font-display text-lg font-semibold text-navy mb-4">Earnings per Share</h3>
            {eps ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs font-medium uppercase tracking-wide text-muted">
                    <th className="px-2 py-2">Particulars</th><th className="px-2 py-2 text-right">CY</th><th className="px-2 py-2 text-right">PY</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Profit after tax (₹)", eps.pat_cy, eps.pat_py],
                    ["Weighted avg shares — Basic", eps.weighted_avg_shares_basic_cy, eps.weighted_avg_shares_basic_py],
                    ["Weighted avg shares — Diluted", eps.weighted_avg_shares_diluted_cy, eps.weighted_avg_shares_diluted_py],
                    ["Basic EPS (₹)", eps.eps_basic_cy, eps.eps_basic_py],
                    ["Diluted EPS (₹)", eps.eps_diluted_cy, eps.eps_diluted_py],
                  ].map((r, i) => (
                    <tr key={i} className={`border-b border-line last:border-0 ${i >= 3 ? "bg-navy-pale/30 font-semibold" : ""}`}>
                      <td className="px-2 py-2 text-ink">{r[0]}</td>
                      <td className="px-2 py-2 text-right font-mono tabular-nums">{r[1] != null ? Number(r[1]).toLocaleString("en-IN") : "—"}</td>
                      <td className="px-2 py-2 text-right font-mono tabular-nums text-muted">{r[2] != null ? Number(r[2]).toLocaleString("en-IN") : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <div className="text-sm text-muted">No EPS data computed.</div>}
          </CardBody>
        </Card>
      </TabPanel>

      <DrillDialog projectId={pid} noteRef={drillNote} onClose={() => setDrillNote(null)} />
    </ProjectPageShell>
  );
}

function StatementCard({ rows, onDrill, editHref, editLabel }: { rows: BSLine[] | null; onDrill: (ref: string) => void; editHref: string; editLabel: string; }) {
  if (rows === null) return <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>;
  if (rows.length === 0) return <Card><CardBody><div className="text-sm text-muted">No data. Upload TB and complete mapping first.</div></CardBody></Card>;
  return (
    <Card>
      <CardBody className="!p-0">
        <div className="flex items-center justify-between px-4 py-3 border-b border-line">
          <h3 className="font-medium text-navy">Statement</h3>
          <Link href={editHref} className="inline-flex items-center gap-1 text-xs text-muted hover:text-ink"><Edit3 className="h-3 w-3" /> Edit {editLabel}</Link>
        </div>
        <table className="w-full text-sm">
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className={`border-b border-line last:border-0 ${r.is_total ? "bg-navy-pale/30 font-semibold" : ""} ${r.is_section ? "bg-surface" : ""}`}>
                <td className={`px-3 py-2 text-ink ${r.is_section ? "font-display font-semibold text-navy" : ""}`} style={{ paddingLeft: `${0.75 + (r.level || 0) * 1}rem` }}>
                  {r.particulars}
                  {r.note_ref && (
                    <button onClick={() => onDrill(r.note_ref!)} className="ml-2 inline-flex items-center gap-0.5 text-xs text-gold hover:underline">
                      Note {r.note_ref} <ExternalLink className="h-3 w-3" />
                    </button>
                  )}
                </td>
                <td className="px-3 py-2 text-right font-mono tabular-nums">{r.cy?.toLocaleString("en-IN") ?? "—"}</td>
                <td className="px-3 py-2 text-right font-mono tabular-nums text-muted">{r.py?.toLocaleString("en-IN") ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardBody>
    </Card>
  );
}

function DrillDialog({ projectId, noteRef, onClose }: { projectId: number; noteRef: string | null; onClose: () => void; }) {
  const [data, setData] = useState<any | null>(null);
  const [loading2, setLoading2] = useState(false);

  useEffect(() => {
    if (!noteRef) { setData(null); return; }
    setLoading2(true);
    generateApi.lineDetail(projectId, noteRef).then(setData).catch(() => setData(null)).finally(() => setLoading2(false));
  }, [noteRef, projectId]);

  return (
    <Dialog open={!!noteRef} onClose={onClose} title={`Note ${noteRef} — TB ledgers behind this line`} size="lg" footer={
      <>
        <Button variant="outline" onClick={onClose}>Close</Button>
        <Link href={`/project/${projectId}/upload`}><Button><ExternalLink className="h-4 w-4" />Open mapping page</Button></Link>
      </>
    }>
      {loading2 ? <div className="text-sm text-muted">Loading…</div>
        : !data ? <div className="text-sm text-muted">No detail available.</div>
        : (
          <div className="space-y-3">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs font-medium uppercase tracking-wide text-muted">
                  <th className="px-2 py-2">Ledger</th><th className="px-2 py-2">CoA</th>
                  <th className="px-2 py-2 text-right">CY Net</th><th className="px-2 py-2 text-right">PY Net</th>
                </tr>
              </thead>
              <tbody>
                {data.ledgers?.map((l: any) => (
                  <tr key={l.tb_row_id} className="border-b border-line last:border-0">
                    <td className="px-2 py-2 text-ink">{l.ledger_name}</td>
                    <td className="px-2 py-2 font-mono text-xs text-navy">{l.coa_code}</td>
                    <td className="px-2 py-2 text-right font-mono tabular-nums">{l.cy_net?.toLocaleString("en-IN")}</td>
                    <td className="px-2 py-2 text-right font-mono tabular-nums text-muted">{l.py_net?.toLocaleString("en-IN")}</td>
                  </tr>
                ))}
                <tr className="bg-navy-pale/40 font-semibold">
                  <td colSpan={2} className="px-2 py-2 text-navy">Total</td>
                  <td className="px-2 py-2 text-right font-mono tabular-nums">{data.cy_total?.toLocaleString("en-IN")}</td>
                  <td className="px-2 py-2 text-right font-mono tabular-nums">{data.py_total?.toLocaleString("en-IN")}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
    </Dialog>
  );
}
