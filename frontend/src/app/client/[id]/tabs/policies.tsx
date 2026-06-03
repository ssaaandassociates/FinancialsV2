"use client";
import { useEffect, useState } from "react";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Plus, Trash2, FileText, Save, Edit3 } from "lucide-react";
import { policiesApi, type Policy } from "@/lib/client-api";

function empty(client_id: number, nextNum: number): Partial<Policy> {
  return { client_id, policy_number: nextNum, title: "", body: "", is_active: true };
}

export function PoliciesTab({ clientId, onChanged }: { clientId: number; onChanged: () => void }) {
  const [rows, setRows] = useState<Policy[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState<Partial<Policy>>({});
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<Policy>>({});

  async function reload() {
    try { setErr(""); setRows(await policiesApi.list(clientId)); }
    catch (e: any) { setErr(e?.message || "Failed to load"); setRows([]); }
  }
  useEffect(() => { reload(); }, [clientId]);

  const nextNum = rows && rows.length ? Math.max(...rows.map((r) => r.policy_number || 0)) + 1 : 1;

  function startAdd() {
    setDraft(empty(clientId, nextNum)); setAdding(true); setEditingId(null);
  }

  async function save(p: Partial<Policy>, id?: number) {
    setBusy(true); setErr("");
    try {
      if (id) await policiesApi.update(id, p); else await policiesApi.create(p);
      setAdding(false); setEditingId(null);
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function remove(id: number) {
    if (!confirm("Remove this policy?")) return;
    try { await policiesApi.remove(id); reload(); onChanged(); }
    catch (e: any) { setErr(e?.message || "Delete failed"); }
  }

  const Form = ({ value, onChange, onSave, onCancel }: any) => (
    <Card>
      <CardBody className="grid gap-4">
        <div className="grid gap-4 sm:grid-cols-[100px_1fr]">
          <div><Label>Number</Label><Input type="number" value={value.policy_number ?? 1} onChange={(e: any) => onChange({ ...value, policy_number: Number(e.target.value) })} /></div>
          <div><Label>Title *</Label><Input value={value.title || ""} onChange={(e: any) => onChange({ ...value, title: e.target.value })} placeholder="e.g. Basis of Preparation" /></div>
        </div>
        <div><Label>Body</Label><Textarea rows={6} value={value.body || ""} onChange={(e: any) => onChange({ ...value, body: e.target.value })} /></div>
        <div className="flex items-center justify-between">
          <Checkbox label="Active (include in this year's financials)" checked={value.is_active !== false} onChange={(e: any) => onChange({ ...value, is_active: e.target.checked })} />
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
            <Button onClick={onSave} disabled={busy || !value.title?.trim()}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Accounting policies</h2>
        <Button variant="gold" onClick={startAdd}><Plus className="h-4 w-4" /> Add policy</Button>
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {adding && <Form value={draft} onChange={setDraft} onSave={() => save(draft)} onCancel={() => setAdding(false)} />}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 && !adding ? (
        <Empty
          icon={<FileText className="h-6 w-6" />}
          title="No accounting policies yet"
          hint="Define once at the client level; reused across all years."
          action={<Button variant="gold" onClick={startAdd}><Plus className="h-4 w-4" /> Add first policy</Button>}
        />
      ) : (
        <div className="space-y-2">
          {rows.sort((a, b) => (a.policy_number || 0) - (b.policy_number || 0)).map((p) =>
            editingId === p.id ? (
              <Form key={p.id} value={editDraft} onChange={setEditDraft} onSave={() => save(editDraft, p.id)} onCancel={() => setEditingId(null)} />
            ) : (
              <Card key={p.id}>
                <CardBody>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-1 gap-3">
                      <div className="rounded-md bg-navy-pale px-2 py-1 text-xs font-mono font-semibold text-navy">{p.policy_number}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <div className="font-medium text-navy">{p.title}</div>
                          {!p.is_active && <Badge tone="neutral">Inactive</Badge>}
                        </div>
                        {p.body && <p className="mt-1.5 whitespace-pre-wrap text-sm text-ink/80">{p.body}</p>}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingId(p.id); setEditDraft({ ...p }); }}><Edit3 className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" onClick={() => remove(p.id)} className="text-danger hover:bg-dangerpale"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                </CardBody>
              </Card>
            )
          )}
        </div>
      )}
    </div>
  );
}
