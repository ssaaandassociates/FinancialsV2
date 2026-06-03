"use client";
import { useEffect, useState } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Plus, Trash2, Users, Save, X, Edit3 } from "lucide-react";
import { directorsApi, type Director } from "@/lib/client-api";

function emptyDir(client_id: number): Partial<Director> {
  return { client_id, name: "", din: "", designation: "Director", date_of_appointment: "", pan: "",
           is_kmp: false, signs_financials: false, is_active: true };
}

// Defined at module level (NOT inside the component) so it is not recreated on
// every render — recreating it remounts the inputs and steals focus after one keystroke.
function DirectorForm({ value, onChange, onSave, onCancel, busy }: {
  value: Partial<Director>;
  onChange: (v: Partial<Director>) => void;
  onSave: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <Card>
      <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2"><Label>Name *</Label><Input value={value.name || ""} onChange={(e) => onChange({ ...value, name: e.target.value })} /></div>
        <div><Label>DIN</Label><Input value={value.din || ""} onChange={(e) => onChange({ ...value, din: e.target.value })} /></div>
        <div><Label>Designation</Label><Input value={value.designation || ""} onChange={(e) => onChange({ ...value, designation: e.target.value })} /></div>
        <div><Label>Date of appointment</Label><Input type="date" value={value.date_of_appointment || ""} onChange={(e) => onChange({ ...value, date_of_appointment: e.target.value })} /></div>
        <div><Label>PAN</Label><Input value={value.pan || ""} onChange={(e) => onChange({ ...value, pan: e.target.value })} /></div>
        <div className="sm:col-span-2 lg:col-span-4 flex flex-wrap items-center gap-4 pt-2">
          <Checkbox label="Is KMP" checked={!!value.is_kmp} onChange={(e) => onChange({ ...value, is_kmp: e.target.checked })} />
          <Checkbox label="Signs financials" checked={!!value.signs_financials} onChange={(e) => onChange({ ...value, signs_financials: e.target.checked })} />
          <Checkbox label="Active" checked={value.is_active !== false} onChange={(e) => onChange({ ...value, is_active: e.target.checked })} />
        </div>
        <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
          <Button onClick={onSave} disabled={busy || !value.name?.trim()}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
        </div>
      </CardBody>
    </Card>
  );
}

export function DirectorsTab({ clientId, onChanged }: { clientId: number; onChanged: () => void }) {
  const [rows, setRows] = useState<Director[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState<Partial<Director>>(emptyDir(clientId));
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<Director>>({});

  async function reload() {
    try { setErr(""); { const _d = await directorsApi.list(clientId); setRows(Array.isArray(_d) ? _d : []); } }
    catch (e: any) { setErr(e?.message || "Failed to load directors"); setRows([]); }
  }
  useEffect(() => { reload(); }, [clientId]);

  async function save(d: Partial<Director>, id?: number) {
    setBusy(true); setErr("");
    try {
      if (id) await directorsApi.update(id, d); else await directorsApi.create(d);
      setAdding(false); setEditingId(null); setDraft(emptyDir(clientId));
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function remove(id: number) {
    if (!confirm("Remove this director?")) return;
    try { await directorsApi.remove(id); reload(); onChanged(); }
    catch (e: any) { setErr(e?.message || "Delete failed"); }
  }

  function startEdit(d: Director) { setEditingId(d.id); setEditDraft({ ...d }); }
  function cancelEdit() { setEditingId(null); setEditDraft({}); }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Directors</h2>
        <Button variant="gold" onClick={() => { setAdding(true); setDraft(emptyDir(clientId)); setEditingId(null); }}>
          <Plus className="h-4 w-4" /> Add director
        </Button>
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {adding && <DirectorForm value={draft} onChange={setDraft} onSave={() => save(draft)} onCancel={() => { setAdding(false); setDraft(emptyDir(clientId)); }} busy={busy} />}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 && !adding ? (
        <Empty
          icon={<Users className="h-6 w-6" />}
          title="No directors yet"
          hint="Add directors to populate KMP and signing block automatically."
          action={<Button variant="gold" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add first director</Button>}
        />
      ) : (
        <div className="space-y-2">
          {rows.map((d) =>
            editingId === d.id ? (
              <DirectorForm key={d.id} value={editDraft} onChange={setEditDraft} onSave={() => save(editDraft, d.id)} onCancel={cancelEdit} busy={busy} />
            ) : (
              <Card key={d.id}>
                <CardBody className="flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="font-medium text-navy">{d.name}</div>
                      {d.is_kmp && <Badge tone="gold">KMP</Badge>}
                      {d.signs_financials && <Badge tone="navy">Signs</Badge>}
                      {!d.is_active && <Badge tone="neutral">Inactive</Badge>}
                    </div>
                    <div className="mt-0.5 text-xs text-muted">
                      {d.designation || "Director"}
                      {d.din && <span className="ml-2 font-mono">DIN {d.din}</span>}
                      {d.date_of_appointment && <span className="ml-2">· appointed {d.date_of_appointment}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => startEdit(d)}><Edit3 className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" onClick={() => remove(d.id)} className="text-danger hover:bg-dangerpale"><Trash2 className="h-4 w-4" /></Button>
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
