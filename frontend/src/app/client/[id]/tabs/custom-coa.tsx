"use client";
import { useEffect, useState } from "react";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Empty } from "@/components/ui/empty";
import { Plus, Trash2, Tag, Save, Edit3 } from "lucide-react";
import { customCoAApi, type CustomCoA } from "@/lib/client-api";

function empty(client_id: number): Partial<CustomCoA> {
  return { client_id, code: "", particulars: "", parent_code: "", nature: "Dr", fs_type: "BS", note_ref: "" };
}

function CustomCoAForm({ value, onChange, onSave, onCancel, busy }: any) {
  return (

    <Card>
      <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div><Label>Code *</Label><Input value={value.code || ""} onChange={(e: any) => onChange({ ...value, code: e.target.value })} placeholder="BS-AS-02-06-99" className="font-mono" /></div>
        <div className="sm:col-span-2"><Label>Particulars *</Label><Input value={value.particulars || ""} onChange={(e: any) => onChange({ ...value, particulars: e.target.value })} placeholder="Custom: Sample Other Current Asset" /></div>
        <div><Label>Parent code</Label><Input value={value.parent_code || ""} onChange={(e: any) => onChange({ ...value, parent_code: e.target.value })} placeholder="BS-AS-02-06" className="font-mono" /></div>
        <div><Label>Nature</Label>
          <Select value={value.nature || "Dr"} onChange={(e: any) => onChange({ ...value, nature: e.target.value })}>
            <option value="Dr">Dr</option><option value="Cr">Cr</option>
          </Select>
        </div>
        <div><Label>FS type</Label>
          <Select value={value.fs_type || "BS"} onChange={(e: any) => onChange({ ...value, fs_type: e.target.value })}>
            <option value="BS">Balance Sheet</option><option value="PL">Profit & Loss</option>
          </Select>
        </div>
        <div><Label>Note ref</Label><Input value={value.note_ref || ""} onChange={(e: any) => onChange({ ...value, note_ref: e.target.value })} /></div>
        <div className="sm:col-span-2 lg:col-span-3 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
          <Button onClick={onSave} disabled={busy || !value.code?.trim() || !value.particulars?.trim()}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
        </div>
      </CardBody>
    </Card>
  
  );
}

export function CustomCoATab({ clientId, onChanged }: { clientId: number; onChanged: () => void }) {
  const [rows, setRows] = useState<CustomCoA[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState<Partial<CustomCoA>>(empty(clientId));
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<CustomCoA>>({});

  async function reload() {
    try { setErr(""); { const _d = await customCoAApi.list(clientId); setRows(Array.isArray(_d) ? _d : []); } }
    catch (e: any) { setErr(e?.message || "Failed to load"); setRows([]); }
  }
  useEffect(() => { reload(); }, [clientId]);

  async function save(c: Partial<CustomCoA>, id?: number) {
    setBusy(true); setErr("");
    try {
      if (id) await customCoAApi.update(id, c); else await customCoAApi.create(c);
      setAdding(false); setEditingId(null); setDraft(empty(clientId));
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function remove(id: number) {
    if (!confirm("Remove this custom code?")) return;
    try { await customCoAApi.remove(id); reload(); onChanged(); }
    catch (e: any) { setErr(e?.message || "Delete failed"); }
  }


  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Custom CoA codes</h2>
        <Button variant="gold" onClick={() => { setAdding(true); setDraft(empty(clientId)); setEditingId(null); }}>
          <Plus className="h-4 w-4" /> Add code
        </Button>
      </div>

      <div className="rounded-lg bg-navy-pale px-4 py-3 text-sm text-navy">
        Custom codes extend the standard 248-code chart for this specific client.
        They appear alongside standard codes in the mapping dropdown.
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {adding && <CustomCoAForm value={draft} onChange={setDraft} onSave={() => save(draft)} onCancel={() => { setAdding(false); setDraft(empty(clientId)); }} busy={busy} />}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 && !adding ? (
        <Empty
          icon={<Tag className="h-6 w-6" />}
          title="No custom codes yet"
          hint="Add codes specific to this client (e.g., a unique expense category)."
          action={<Button variant="gold" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add first code</Button>}
        />
      ) : (
        <Card>
          <CardBody className="!p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line text-left text-xs font-medium uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Particulars</th>
                  <th className="px-4 py-3">Parent</th>
                  <th className="px-4 py-3">Nature</th>
                  <th className="px-4 py-3">FS</th>
                  <th className="px-4 py-3">Note</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => editingId === c.id ? (
                  <tr key={c.id}><td colSpan={7} className="p-4">
                    <CustomCoAForm value={editDraft} onChange={setEditDraft} onSave={() => save(editDraft, c.id)} onCancel={() => { setEditingId(null); setEditDraft({}); }} busy={busy} />
                  </td></tr>
                ) : (
                  <tr key={c.id} className="border-b border-line text-sm last:border-0">
                    <td className="px-4 py-3 font-mono font-medium text-navy">{c.code}</td>
                    <td className="px-4 py-3 text-ink">{c.particulars}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted">{c.parent_code || "—"}</td>
                    <td className="px-4 py-3 text-sm">{c.nature || "—"}</td>
                    <td className="px-4 py-3 text-sm">{c.fs_type || "—"}</td>
                    <td className="px-4 py-3 text-sm">{c.note_ref || "—"}</td>
                    <td className="px-4 py-3"><div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingId(c.id); setEditDraft({ ...c }); }}><Edit3 className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" onClick={() => remove(c.id)} className="text-danger hover:bg-dangerpale"><Trash2 className="h-4 w-4" /></Button>
                    </div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
