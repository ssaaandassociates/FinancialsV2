"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Dialog } from "@/components/ui/dialog";
import { Plus, Copy, Trash2, FolderOpen, ChevronRight } from "lucide-react";
import { projectsApi, type ProjectRow } from "@/lib/client-api";

export function ProjectsTab({ clientId, onChanged }: { clientId: number; onChanged: () => void }) {
  const [rows, setRows] = useState<ProjectRow[] | null>(null);
  const [err, setErr] = useState("");
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);

  const [fy, setFy] = useState("2024-25");
  const [bsCY, setBsCY] = useState("2025-03-31");
  const [bsPY, setBsPY] = useState("2024-03-31");
  const [companyType, setCompanyType] = useState("manufacturing");

  // Delete confirmation
  const [delId, setDelId] = useState<number | null>(null);
  const [delBusy, setDelBusy] = useState(false);

  async function reload() {
    try {
      setErr("");
      const data = await projectsApi.list(clientId);
      setRows(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setErr(e?.message || "Failed to load projects");
      setRows([]);
    }
  }
  useEffect(() => { reload(); }, [clientId]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      await projectsApi.create({ client_id: clientId, financial_year: fy, bs_date_cy: bsCY, bs_date_py: bsPY, company_type: companyType });
      setCreating(false);
      reload(); onChanged();
    } catch (e: any) {
      setErr(e?.message || "Create failed");
    } finally { setBusy(false); }
  }

  async function duplicate(id: number) {
    setBusy(true); setErr("");
    try {
      await projectsApi.duplicate(id);
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Duplicate failed"); }
    finally { setBusy(false); }
  }

  async function doDelete() {
    if (delId == null) return;
    setDelBusy(true);
    try {
      await projectsApi.remove(delId);
      setDelId(null);
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Delete failed"); }
    finally { setDelBusy(false); }
  }

  const statusTone = (s: string) => s === "ready" ? "ok" : s === "filed" ? "neutral" : "gold";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Projects</h2>
        <Button variant="gold" onClick={() => setCreating((v) => !v)}>
          <Plus className="h-4 w-4" /> {creating ? "Cancel" : "New project"}
        </Button>
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {creating && (
        <Card className="rise">
          <CardHeader><h3 className="font-medium text-navy">Create project</h3></CardHeader>
          <CardBody>
            <form onSubmit={create} className="grid gap-4 sm:grid-cols-4">
              <div><Label>Financial year *</Label><Input value={fy} onChange={(e) => setFy(e.target.value)} placeholder="2024-25" required /></div>
              <div><Label>BS date CY *</Label><Input type="date" value={bsCY} onChange={(e) => setBsCY(e.target.value)} required /></div>
              <div><Label>BS date PY *</Label><Input type="date" value={bsPY} onChange={(e) => setBsPY(e.target.value)} required /></div>
              <div><Label>Company type</Label>
                <Select value={companyType} onChange={(e) => setCompanyType(e.target.value)}>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="trading">Trading</option>
                  <option value="service">Service</option>
                </Select>
              </div>
              <div className="sm:col-span-4 flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setCreating(false)} disabled={busy} type="button">Cancel</Button>
                <Button type="submit" disabled={busy}>{busy ? "Creating…" : "Create"}</Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 ? (
        <Empty
          icon={<FolderOpen className="h-6 w-6" />}
          title="No projects yet"
          hint="Each project = one financial year for this client."
          action={<Button variant="gold" onClick={() => setCreating(true)}><Plus className="h-4 w-4" /> Create first project</Button>}
        />
      ) : (
        <div className="space-y-2">
          {rows.map((p) => (
            <Card key={p.id}>
              <CardBody className="flex items-center justify-between gap-4">
                <Link href={`/project/${p.id}`} className="flex flex-1 items-center gap-4 group">
                  <div className="rounded-lg bg-navy-pale p-2 text-navy">
                    <FolderOpen className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-navy group-hover:text-gold">FY {p.financial_year}</div>
                    <div className="mt-0.5 text-xs text-muted">
                      {p.bs_date_cy ? `as at ${p.bs_date_cy}` : "—"} {p.company_type ? `· ${p.company_type}` : ""}
                    </div>
                  </div>
                  <Badge tone={statusTone(p.status) as any}>{p.status}</Badge>
                  <ChevronRight className="h-4 w-4 text-muted" />
                </Link>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => duplicate(p.id)} title="Duplicate" disabled={busy}>
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setDelId(p.id)} className="text-danger hover:bg-dangerpale" title="Delete">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Dialog
        open={delId !== null}
        onClose={() => setDelId(null)}
        title="Delete this project?"
        footer={<>
          <Button variant="outline" onClick={() => setDelId(null)}>Cancel</Button>
          <Button variant="danger" onClick={doDelete} disabled={delBusy}>{delBusy ? "Deleting…" : "Delete project"}</Button>
        </>}
      >
        <div className="text-sm text-ink">
          This deletes the project and all its trial balance, mappings, audit entries, and supplementary
          records. The client's master data is unaffected. This cannot be undone.
        </div>
      </Dialog>
    </div>
  );
}
