"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Empty } from "@/components/ui/empty";
import { Plus, Trash2, Save, Edit3, Check, AlertCircle, Download, FileText } from "lucide-react";
import { auditApi, type AuditEntry } from "@/lib/project-api";
import { backendUrl } from "@/lib/api";

function empty(project_id: number): Partial<AuditEntry> {
  return { project_id, date: new Date().toISOString().slice(0,10), description: "", dr_coa_code: "", cr_coa_code: "", amount: 0, status: "proposed" };
}

function AuditForm({ value, onChange, onSave, onCancel, busy }: any) {
  return (

    <Card>
      <CardBody className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <div><Label>Date</Label><Input type="date" value={value.date || ""} onChange={(e: any) => onChange({ ...value, date: e.target.value })} /></div>
        <div className="lg:col-span-3"><Label>Description *</Label><Input value={value.description || ""} onChange={(e: any) => onChange({ ...value, description: e.target.value })} /></div>
        <div><Label>Amount *</Label><Input type="number" value={value.amount ?? 0} onChange={(e: any) => onChange({ ...value, amount: Number(e.target.value) })} /></div>
        <div>
          <Label>Status</Label>
          <Select value={value.status || "proposed"} onChange={(e: any) => onChange({ ...value, status: e.target.value })}>
            <option value="proposed">Proposed</option><option value="approved">Approved</option><option value="posted">Posted</option>
          </Select>
        </div>
        <div className="lg:col-span-3"><Label>Dr CoA Code *</Label><Input value={value.dr_coa_code || ""} onChange={(e: any) => onChange({ ...value, dr_coa_code: e.target.value })} className="font-mono" placeholder="e.g. PL-04-05" /></div>
        <div className="lg:col-span-3"><Label>Cr CoA Code *</Label><Input value={value.cr_coa_code || ""} onChange={(e: any) => onChange({ ...value, cr_coa_code: e.target.value })} className="font-mono" placeholder="e.g. BS-EL-04-02-09" /></div>
        <div className="lg:col-span-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
          <Button onClick={onSave} disabled={busy || !value.description || !value.dr_coa_code || !value.cr_coa_code}>
            <Save className="h-4 w-4" />{busy ? "Saving…" : "Save entry"}
          </Button>
        </div>
      </CardBody>
    </Card>
  
  );
}

export default function AuditPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [rows, setRows] = useState<AuditEntry[] | null>(null);
  const [check, setCheck] = useState<{ total: number; balanced: boolean; dr_total: number; cr_total: number } | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "proposed" | "approved" | "posted">("all");
  const [draft, setDraft] = useState<Partial<AuditEntry>>(empty(projectId));
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<AuditEntry>>({});

  async function reload() {
    try {
      setErr("");
      const [list, chk] = await Promise.all([auditApi.list(projectId), auditApi.check(projectId)]);
      setRows(list); setCheck(chk);
    } catch (e: any) { setErr(e?.message || "Failed to load"); setRows([]); }
  }
  useEffect(() => { if (session) reload(); }, [session, projectId]);

  async function save(e: Partial<AuditEntry>, id?: number) {
    setBusy(true); setErr("");
    try {
      if (id) await auditApi.update(id, e); else await auditApi.create({ ...e, project_id: projectId });
      setAdding(false); setEditingId(null); setDraft(empty(projectId));
      reload();
    } catch (er: any) { setErr(er?.message || "Save failed"); }
    finally { setBusy(false); }
  }
  async function remove(id: number) {
    if (!confirm("Delete this entry?")) return;
    try { await auditApi.remove(id); reload(); } catch (e: any) { setErr(e?.message || "Delete failed"); }
  }
  async function setStatus(e: AuditEntry, status: "proposed" | "approved" | "posted") {
    try { await auditApi.update(e.id, { status }); reload(); } catch (er: any) { setErr(er?.message || "Status update failed"); }
  }


  if (loading || !session) return null;

  return (
    <ProjectPageShell
      projectId={projectId}
      title="Audit entries"
      actions={
        <div className="flex items-center gap-3">
          {check && (
            <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${check.balanced ? "text-ok" : "text-danger"}`}>
              {check.balanced ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
              {check.balanced ? `Balanced (\u20B9${check.dr_total.toLocaleString("en-IN")})` : `Out by \u20B9${(check.dr_total - check.cr_total).toLocaleString("en-IN")}`}
            </span>
          )}
          <a href={backendUrl(`/audit/${projectId}/export`)} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-medium hover:bg-surface">
            <Download className="h-3.5 w-3.5" /> Export
          </a>
          <Button size="sm" variant="gold" onClick={() => { setAdding(true); setDraft(empty(projectId)); setEditingId(null); }}>
            <Plus className="h-4 w-4" /> New entry
          </Button>
        </div>
      }
    >
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}
      {adding && <div className="mb-4"><AuditForm value={draft} onChange={setDraft} onSave={() => save(draft)} onCancel={() => setAdding(false)} busy={busy} /></div>}

      {rows && rows.length > 0 && (
        <Card className="mb-4">
          <CardBody className="flex flex-wrap items-center gap-3">
            <div className="flex gap-1">
              {(["all", "proposed", "approved", "posted"] as const).map((s) => (
                <button key={s} onClick={() => setStatusFilter(s)}
                        className={`rounded-full border border-line px-3 py-1 text-xs font-medium transition-colors ${statusFilter === s ? "bg-navy text-white" : "bg-white text-ink hover:bg-surface"}`}>
                  {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
                </button>
              ))}
            </div>
            <div className="flex-1 min-w-[200px]">
              <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search description, Dr CoA, or Cr CoA…" />
            </div>
          </CardBody>
        </Card>
      )}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 && !adding ? (
        <Empty icon={<FileText className="h-6 w-6" />} title="No audit entries yet" hint="Add adjusting journal entries to bring the books to final balances."
               action={<Button variant="gold" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add first entry</Button>} />
      ) : (
        <Card>
          <CardBody className="!p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Date</th><th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Dr CoA</th><th className="px-4 py-3">Cr CoA</th>
                  <th className="px-4 py-3 text-right">Amount</th><th className="px-4 py-3">Status</th><th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {rows.filter((r) => {
                  if (statusFilter !== "all" && r.status !== statusFilter) return false;
                  const q = search.trim().toLowerCase();
                  if (!q) return true;
                  return (r.description || "").toLowerCase().includes(q)
                      || (r.dr_coa_code || "").toLowerCase().includes(q)
                      || (r.cr_coa_code || "").toLowerCase().includes(q);
                }).map((r) => editingId === r.id ? (
                  <tr key={r.id}><td colSpan={7} className="p-3 bg-surface/30">
                    <AuditForm value={editDraft} onChange={setEditDraft} onSave={() => save(editDraft, r.id)} onCancel={() => setEditingId(null)} busy={busy} />
                  </td></tr>
                ) : (
                  <tr key={r.id} className="border-b border-line last:border-0">
                    <td className="px-4 py-3 text-muted">{r.date || "—"}</td>
                    <td className="px-4 py-3 font-medium text-ink">{r.description}</td>
                    <td className="px-4 py-3 font-mono text-xs text-navy">{r.dr_coa_code}</td>
                    <td className="px-4 py-3 font-mono text-xs text-navy">{r.cr_coa_code}</td>
                    <td className="px-4 py-3 text-right font-mono tabular-nums">{r.amount?.toLocaleString("en-IN")}</td>
                    <td className="px-4 py-3">
                      <Select value={r.status} onChange={(e) => setStatus(r, e.target.value as any)} className="!h-7 !text-xs !w-28">
                        <option value="proposed">Proposed</option><option value="approved">Approved</option><option value="posted">Posted</option>
                      </Select>
                    </td>
                    <td className="px-4 py-3"><div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingId(r.id); setEditDraft({ ...r }); }}><Edit3 className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" className="text-danger hover:bg-dangerpale" onClick={() => remove(r.id)}><Trash2 className="h-4 w-4" /></Button>
                    </div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardBody>
        </Card>
      )}
    </ProjectPageShell>
  );
}
