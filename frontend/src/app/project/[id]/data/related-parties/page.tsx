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
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Dialog } from "@/components/ui/dialog";
import { Plus, Trash2, ChevronDown, ChevronRight, Users, Sparkles, Save, Edit3 } from "lucide-react";
import { rpApi, type RelatedParty, type RPTransaction, type KMPCandidate } from "@/lib/project-api";

const CATS = ["KMP", "Director", "Holding", "Subsidiary", "Associate", "Joint Venture", "Enterprise where KMP has significant influence", "Other"];
const STD_TXNS = ["Sales", "Purchases", "Services received", "Services rendered", "Remuneration", "Sitting fees", "Loan given", "Loan taken", "Interest income", "Interest expense", "Rent paid", "Rent received", "Reimbursement", "Director's commission", "Other"];

export default function RPPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [parties, setParties] = useState<RelatedParty[] | null>(null);
  const [txnsByParty, setTxnsByParty] = useState<Record<number, RPTransaction[]>>({});
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [showAdd, setShowAdd] = useState(false);
  const [kmpOpts, setKmpOpts] = useState<KMPCandidate[]>([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    try {
      setErr("");
      const list = await rpApi.listParties(pid);
      setParties(Array.isArray(list) ? list : []);
    } catch (e: any) { setErr(e?.message || "Failed to load"); setParties([]); }
  }
  useEffect(() => { if (session) reload(); }, [session, pid]);

  async function loadTxns(partyId: number) {
    try {
      const t = await rpApi.txnsForParty(partyId);
      setTxnsByParty((prev) => ({ ...prev, [partyId]: Array.isArray(t) ? t : [] }));
    } catch (e: any) { setErr(e?.message || "Failed to load txns"); }
  }

  function toggle(id: number) {
    setExpanded((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id); else { n.add(id); loadTxns(id); }
      return n;
    });
  }

  async function autoKMP() {
    setBusy(true);
    try { const r = await rpApi.autoKMP(pid); setErr(""); if (r.added === 0) setErr("No new KMP found. Mark directors as KMP in client master."); reload(); }
    catch (e: any) { setErr(e?.message || "Auto-KMP failed"); }
    finally { setBusy(false); }
  }

  async function openAdd() {
    setShowAdd(true);
    try { const k = await rpApi.kmpCandidates(pid); setKmpOpts(Array.isArray(k) ? k : []); } catch {}
  }

  if (loading || !session) return null;

  return (
    <ProjectPageShell projectId={pid} title="Related Parties"
      actions={
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={autoKMP} disabled={busy}><Sparkles className="h-4 w-4" /> Auto-add KMP</Button>
          <Button size="sm" variant="gold" onClick={openAdd}><Plus className="h-4 w-4" /> Add party</Button>
        </div>
      }>
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      {parties === null ? <Card><CardBody><div className="text-sm text-muted">Loading…</div></CardBody></Card>
        : parties.length === 0 ? <Empty icon={<Users className="h-6 w-6" />} title="No related parties yet" hint="Add KMP, holding/subsidiary/associate entities."
            action={<Button variant="gold" onClick={openAdd}><Plus className="h-4 w-4" /> Add first party</Button>} />
        : <div className="space-y-2">
            {parties.map((p) => (
              <PartyRow key={p.id} party={p} expanded={expanded.has(p.id)} onToggle={() => toggle(p.id)}
                txns={txnsByParty[p.id]} onTxnsChanged={() => loadTxns(p.id)} onRemoveParty={async () => {
                  if (!confirm(`Remove ${p.name}?`)) return;
                  await rpApi.removeParty(p.id); reload();
                }} />
            ))}
          </div>
      }
      <AddPartyDialog open={showAdd} onClose={() => setShowAdd(false)} projectId={pid} kmpOpts={kmpOpts} onAdded={reload} />
    </ProjectPageShell>
  );
}

function PartyRow({ party, expanded, onToggle, txns, onTxnsChanged, onRemoveParty }: {
  party: RelatedParty; expanded: boolean; onToggle: () => void;
  txns?: RPTransaction[]; onTxnsChanged: () => void; onRemoveParty: () => void;
}) {
  const [addingTxn, setAddingTxn] = useState(false);
  const [draft, setDraft] = useState<Partial<RPTransaction>>({ project_id: party.project_id, party_id: party.id, transaction_type: "Sales", cy_amount: 0, py_amount: 0 });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Partial<RPTransaction>>({});
  const [customType, setCustomType] = useState(false);

  async function saveTxn(t: Partial<RPTransaction>, id?: number) {
    if (id) await rpApi.updateTxn(id, t);
    else await rpApi.createTxn(t);
    setAddingTxn(false); setEditingId(null);
    setDraft({ project_id: party.project_id, party_id: party.id, transaction_type: "Sales", cy_amount: 0, py_amount: 0 });
    onTxnsChanged();
  }
  async function removeTxn(id: number) {
    if (!confirm("Remove this transaction?")) return;
    await rpApi.removeTxn(id); onTxnsChanged();
  }

  return (
    <Card>
      <CardBody className={expanded ? "!pb-3" : undefined}>
        <div className="flex items-center gap-3">
          <button onClick={onToggle} className="text-muted hover:text-ink">
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <div className="font-medium text-navy">{party.name}</div>
              <Badge tone="gold">{party.category}</Badge>
              {party.relationship && <span className="text-xs text-muted">· {party.relationship}</span>}
            </div>
          </div>
          {txns && <span className="text-xs text-muted">{txns.length} txn{txns.length !== 1 ? "s" : ""}</span>}
          <Button variant="ghost" size="sm" className="text-danger hover:bg-dangerpale" onClick={onRemoveParty}><Trash2 className="h-4 w-4" /></Button>
        </div>

        {expanded && (
          <div className="mt-3 border-t border-line pt-3">
            {!txns ? <div className="text-sm text-muted">Loading…</div>
              : <>
                  <div className="space-y-1.5">
                    {txns.map((t) => editingId === t.id ? (
                      <div key={t.id} className="rounded-lg border border-gold bg-gold-light/30 p-3 grid gap-2 sm:grid-cols-4 items-end">
                        <div><Label>Type</Label><Input value={editDraft.transaction_type || ""} onChange={(e) => setEditDraft({ ...editDraft, transaction_type: e.target.value })} /></div>
                        <div><Label>CY ₹</Label><Input type="number" value={editDraft.cy_amount ?? 0} onChange={(e) => setEditDraft({ ...editDraft, cy_amount: Number(e.target.value) })} /></div>
                        <div><Label>PY ₹</Label><Input type="number" value={editDraft.py_amount ?? 0} onChange={(e) => setEditDraft({ ...editDraft, py_amount: Number(e.target.value) })} /></div>
                        <div className="flex gap-1 justify-end">
                          <Button size="sm" onClick={() => saveTxn(editDraft, t.id)}><Save className="h-3 w-3" /></Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>Cancel</Button>
                        </div>
                      </div>
                    ) : (
                      <div key={t.id} className="flex items-center gap-3 rounded-lg bg-surface/60 px-3 py-2 text-sm">
                        <div className="flex-1 text-ink">{t.transaction_type}</div>
                        <div className="w-28 text-right font-mono tabular-nums">{(t.cy_amount ?? t.cy ?? 0).toLocaleString("en-IN")}</div>
                        <div className="w-28 text-right font-mono tabular-nums text-muted">{(t.py_amount ?? t.py ?? 0).toLocaleString("en-IN")}</div>
                        <Button variant="ghost" size="sm" onClick={() => { setEditingId(t.id); setEditDraft({ ...t }); }}><Edit3 className="h-3 w-3" /></Button>
                        <Button variant="ghost" size="sm" className="text-danger hover:bg-dangerpale" onClick={() => removeTxn(t.id)}><Trash2 className="h-3 w-3" /></Button>
                      </div>
                    ))}
                  </div>

                  {addingTxn ? (
                    <div className="mt-2 rounded-lg border border-gold bg-gold-light/30 p-3 grid gap-2 sm:grid-cols-4 items-end">
                      <div>
                        <Label>Type</Label>
                        {!customType ? (
                          <Select value={draft.transaction_type || "Sales"} onChange={(e) => { if (e.target.value === "__custom") setCustomType(true); else setDraft({ ...draft, transaction_type: e.target.value }); }}>
                            {STD_TXNS.map((t) => <option key={t} value={t}>{t}</option>)}
                            <option value="__custom">— Custom —</option>
                          </Select>
                        ) : (
                          <Input value={draft.transaction_type || ""} onChange={(e) => setDraft({ ...draft, transaction_type: e.target.value })} placeholder="Custom type" />
                        )}
                      </div>
                      <div><Label>CY ₹</Label><Input type="number" value={draft.cy_amount ?? 0} onChange={(e) => setDraft({ ...draft, cy_amount: Number(e.target.value) })} /></div>
                      <div><Label>PY ₹</Label><Input type="number" value={draft.py_amount ?? 0} onChange={(e) => setDraft({ ...draft, py_amount: Number(e.target.value) })} /></div>
                      <div className="flex gap-1 justify-end">
                        <Button size="sm" onClick={() => saveTxn(draft)}><Save className="h-3 w-3" /> Add</Button>
                        <Button size="sm" variant="ghost" onClick={() => { setAddingTxn(false); setCustomType(false); }}>Cancel</Button>
                      </div>
                    </div>
                  ) : (
                    <Button size="sm" variant="outline" className="mt-2" onClick={() => setAddingTxn(true)}><Plus className="h-3 w-3" /> Add transaction</Button>
                  )}
                </>
            }
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function AddPartyDialog({ open, onClose, projectId, kmpOpts, onAdded }: { open: boolean; onClose: () => void; projectId: number; kmpOpts: KMPCandidate[]; onAdded: () => void; }) {
  const [name, setName] = useState("");
  const [category, setCategory] = useState("KMP");
  const [relationship, setRelationship] = useState("");
  const [busy, setBusy] = useState(false);
  const [pickFromMaster, setPickFromMaster] = useState(false);

  useEffect(() => { if (!open) { setName(""); setCategory("KMP"); setRelationship(""); setPickFromMaster(false); } }, [open]);

  async function save() {
    if (!name) return;
    setBusy(true);
    try { await rpApi.createParty({ project_id: projectId, name, category: category as any, relationship }); onAdded(); onClose(); }
    catch {} finally { setBusy(false); }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Add related party" footer={
      <>
        <Button variant="outline" onClick={onClose}>Cancel</Button>
        <Button onClick={save} disabled={!name || busy}>{busy ? "Adding…" : "Add party"}</Button>
      </>
    }>
      <div className="space-y-3 text-sm">
        {kmpOpts.length > 0 && (
          <div>
            <Label>Pick from client master (optional)</Label>
            <Select value="" onChange={(e) => {
              const i = Number(e.target.value); if (Number.isFinite(i) && kmpOpts[i]) {
                setName(kmpOpts[i].name); setCategory(kmpOpts[i].category_suggestion); setRelationship(kmpOpts[i].designation || "");
                setPickFromMaster(true);
              }
            }}>
              <option value="">— Select —</option>
              {kmpOpts.map((k, i) => <option key={i} value={i}>{k.name} ({k.category_suggestion})</option>)}
            </Select>
          </div>
        )}
        <div><Label>Name *</Label><Input value={name} onChange={(e) => setName(e.target.value)} /></div>
        <div><Label>Category</Label>
          <Select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATS.map((c) => <option key={c} value={c}>{c}</option>)}
          </Select>
        </div>
        <div><Label>Relationship / Designation</Label><Input value={relationship} onChange={(e) => setRelationship(e.target.value)} placeholder="e.g. Whole-time Director" /></div>
      </div>
    </Dialog>
  );
}
