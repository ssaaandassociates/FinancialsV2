"use client";
import { useEffect, useState } from "react";
import { Card, CardBody } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Plus, Trash2, Building2, Save, Edit3 } from "lucide-react";
import { shareholdersApi, type Shareholder } from "@/lib/client-api";

function empty(client_id: number): Partial<Shareholder> {
  return { client_id, name: "", no_of_shares_cy: 0, no_of_shares_py: 0, face_value: 10,
           pct_holding_cy: 0, pct_holding_py: 0, is_promoter: false, is_director: false, din: "", pan: "" };
}

export function ShareholdersTab({ clientId, onChanged }: { clientId: number; onChanged: () => void }) {
  const [rows, setRows] = useState<Shareholder[] | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draft, setDraft] = useState<Partial<Shareholder>>(empty(clientId));
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<Shareholder>>({});

  async function reload() {
    try { setErr(""); setRows(await shareholdersApi.list(clientId)); }
    catch (e: any) { setErr(e?.message || "Failed to load"); setRows([]); }
  }
  useEffect(() => { reload(); }, [clientId]);

  async function save(s: Partial<Shareholder>, id?: number) {
    setBusy(true); setErr("");
    try {
      if (id) await shareholdersApi.update(id, s); else await shareholdersApi.create(s);
      setAdding(false); setEditingId(null); setDraft(empty(clientId));
      reload(); onChanged();
    } catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function remove(id: number) {
    if (!confirm("Remove this shareholder?")) return;
    try { await shareholdersApi.remove(id); reload(); onChanged(); }
    catch (e: any) { setErr(e?.message || "Delete failed"); }
  }

  const Form = ({ value, onChange, onSave, onCancel }: any) => (
    <Card>
      <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2"><Label>Name *</Label><Input value={value.name || ""} onChange={(e: any) => onChange({ ...value, name: e.target.value })} /></div>
        <div><Label>PAN</Label><Input value={value.pan || ""} onChange={(e: any) => onChange({ ...value, pan: e.target.value })} /></div>
        <div><Label>Face value</Label><Input type="number" value={value.face_value ?? 10} onChange={(e: any) => onChange({ ...value, face_value: Number(e.target.value) })} /></div>
        <div><Label>No. of shares (CY)</Label><Input type="number" value={value.no_of_shares_cy ?? 0} onChange={(e: any) => onChange({ ...value, no_of_shares_cy: Number(e.target.value) })} /></div>
        <div><Label>No. of shares (PY)</Label><Input type="number" value={value.no_of_shares_py ?? 0} onChange={(e: any) => onChange({ ...value, no_of_shares_py: Number(e.target.value) })} /></div>
        <div><Label>% holding (CY)</Label><Input type="number" step="0.01" value={value.pct_holding_cy ?? 0} onChange={(e: any) => onChange({ ...value, pct_holding_cy: Number(e.target.value) })} /></div>
        <div><Label>% holding (PY)</Label><Input type="number" step="0.01" value={value.pct_holding_py ?? 0} onChange={(e: any) => onChange({ ...value, pct_holding_py: Number(e.target.value) })} /></div>
        <div className="sm:col-span-2 lg:col-span-4 flex flex-wrap gap-4 pt-2">
          <Checkbox label="Is promoter" checked={!!value.is_promoter} onChange={(e: any) => onChange({ ...value, is_promoter: e.target.checked })} />
          <Checkbox label="Is director (auto-link)" checked={!!value.is_director} onChange={(e: any) => onChange({ ...value, is_director: e.target.checked })} />
          {value.is_director && (
            <div className="flex-1 min-w-[180px]"><Input placeholder="DIN" value={value.din || ""} onChange={(e: any) => onChange({ ...value, din: e.target.value })} /></div>
          )}
        </div>
        <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
          <Button onClick={onSave} disabled={busy || !value.name?.trim()}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
        </div>
      </CardBody>
    </Card>
  );

  const fmtPct = (n?: number) => n != null ? `${Number(n).toFixed(2)}%` : "—";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Shareholders</h2>
        <Button variant="gold" onClick={() => { setAdding(true); setDraft(empty(clientId)); setEditingId(null); }}>
          <Plus className="h-4 w-4" /> Add shareholder
        </Button>
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {adding && <Form value={draft} onChange={setDraft} onSave={() => save(draft)} onCancel={() => { setAdding(false); setDraft(empty(clientId)); }} />}

      {rows === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
      ) : rows.length === 0 && !adding ? (
        <Empty
          icon={<Building2 className="h-6 w-6" />}
          title="No shareholders yet"
          hint="Include promoters and those holding >5%."
          action={<Button variant="gold" onClick={() => setAdding(true)}><Plus className="h-4 w-4" /> Add first shareholder</Button>}
        />
      ) : (
        <Card>
          <CardBody className="!p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line text-left text-xs font-medium uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3 text-right">Shares CY</th>
                  <th className="px-4 py-3 text-right">Shares PY</th>
                  <th className="px-4 py-3 text-right">% CY</th>
                  <th className="px-4 py-3 text-right">% PY</th>
                  <th className="px-4 py-3">Flags</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => editingId === s.id ? (
                  <tr key={s.id}><td colSpan={7} className="p-4">
                    <Form value={editDraft} onChange={setEditDraft} onSave={() => save(editDraft, s.id)} onCancel={() => { setEditingId(null); setEditDraft({}); }} />
                  </td></tr>
                ) : (
                  <tr key={s.id} className="border-b border-line text-sm last:border-0">
                    <td className="px-4 py-3 font-medium text-ink">{s.name}{s.pan && <div className="font-mono text-xs text-muted">{s.pan}</div>}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{s.no_of_shares_cy?.toLocaleString("en-IN") ?? "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{s.no_of_shares_py?.toLocaleString("en-IN") ?? "—"}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{fmtPct(s.pct_holding_cy)}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{fmtPct(s.pct_holding_py)}</td>
                    <td className="px-4 py-3"><div className="flex gap-1">
                      {s.is_promoter && <Badge tone="gold">Promoter</Badge>}
                      {s.is_director && <Badge tone="navy">Director</Badge>}
                    </div></td>
                    <td className="px-4 py-3"><div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => { setEditingId(s.id); setEditDraft({ ...s }); }}><Edit3 className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="sm" onClick={() => remove(s.id)} className="text-danger hover:bg-dangerpale"><Trash2 className="h-4 w-4" /></Button>
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
