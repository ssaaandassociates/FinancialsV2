"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, Save } from "lucide-react";
import { signingApi, type SigningBlock, profileApi, type CompanyProfile, disclosuresApi, type DisclosureSection } from "@/lib/project-api";

export default function SigningPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [block, setBlock] = useState<SigningBlock | null>(null);
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [disc, setDisc] = useState<Record<string, DisclosureSection> | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  async function reload() {
    try {
      setErr("");
      const [b, p, d] = await Promise.all([
        signingApi.get(pid).catch(() => ({ project_id: pid } as SigningBlock)),
        profileApi.get(pid).catch(() => ({ project_id: pid } as CompanyProfile)),
        disclosuresApi.list(pid).catch(() => ({})),
      ]);
      setBlock(b); setProfile(p); setDisc(d || {});
    } catch (e: any) { setErr(e?.message || "Failed to load"); }
  }
  useEffect(() => { if (session) reload(); }, [session, pid]);

  async function autoFill() {
    setBusy(true); setMsg("");
    try { await signingApi.autoPopulate(pid); await reload(); setMsg("Auto-filled from client master."); setTimeout(() => setMsg(""), 2500); }
    catch (e: any) { setErr(e?.message || "Auto-fill failed"); }
    finally { setBusy(false); }
  }

  async function saveBlock() {
    if (!block) return;
    setBusy(true); setMsg("");
    try { await signingApi.save(block); setMsg("Signing block saved."); setTimeout(() => setMsg(""), 2500); }
    catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }
  async function saveProfile() {
    if (!profile) return;
    setBusy(true); setMsg("");
    try { await profileApi.save(profile); setMsg("Disclosures saved."); setTimeout(() => setMsg(""), 2500); }
    catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function updDiscItem(itemId: number, field: "cy" | "py" | "notes", value: any) {
    const data: any = { [field]: value };
    try { await disclosuresApi.updateItem(itemId, data); }
    catch (e: any) { setErr(e?.message || "Save failed"); }
  }

  if (loading || !session) return null;

  return (
    <ProjectPageShell projectId={pid} title="Signing & Disclosures">
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}
      {msg && <div className="mb-4 rounded-lg bg-okpale px-3 py-2 text-sm text-ok">{msg}</div>}

      {/* Signing block */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="font-medium text-navy">Signing block</h3>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={autoFill} disabled={busy}><Sparkles className="h-4 w-4" /> Auto-fill from client</Button>
              <Button size="sm" onClick={saveBlock} disabled={busy}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
            </div>
          </div>
        </CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-3">
          <div><Label>Auditor firm</Label><Input value={block?.auditor_firm || ""} onChange={(e) => setBlock({ ...block!, auditor_firm: e.target.value })} /></div>
          <div><Label>FRN</Label><Input value={block?.auditor_frn || ""} onChange={(e) => setBlock({ ...block!, auditor_frn: e.target.value })} /></div>
          <div><Label>Partner name</Label><Input value={block?.auditor_partner || ""} onChange={(e) => setBlock({ ...block!, auditor_partner: e.target.value })} /></div>
          <div><Label>Partner M.No.</Label><Input value={block?.auditor_membership_no || ""} onChange={(e) => setBlock({ ...block!, auditor_membership_no: e.target.value })} /></div>
          <div><Label>UDIN</Label><Input value={block?.udin || ""} onChange={(e) => setBlock({ ...block!, udin: e.target.value })} /></div>
          <div><Label>Place</Label><Input value={block?.place || ""} onChange={(e) => setBlock({ ...block!, place: e.target.value })} /></div>
          <div><Label>Date</Label><Input type="date" value={block?.date || ""} onChange={(e) => setBlock({ ...block!, date: e.target.value })} /></div>

          <div className="sm:col-span-3 border-t border-line pt-3 mt-1"><div className="text-xs font-medium uppercase tracking-wide text-muted">Director 1</div></div>
          <div><Label>Name</Label><Input value={block?.director1_name || ""} onChange={(e) => setBlock({ ...block!, director1_name: e.target.value })} /></div>
          <div><Label>DIN</Label><Input value={block?.director1_din || ""} onChange={(e) => setBlock({ ...block!, director1_din: e.target.value })} /></div>
          <div><Label>Designation</Label><Input value={block?.director1_designation || ""} onChange={(e) => setBlock({ ...block!, director1_designation: e.target.value })} /></div>

          <div className="sm:col-span-3 border-t border-line pt-3 mt-1"><div className="text-xs font-medium uppercase tracking-wide text-muted">Director 2</div></div>
          <div><Label>Name</Label><Input value={block?.director2_name || ""} onChange={(e) => setBlock({ ...block!, director2_name: e.target.value })} /></div>
          <div><Label>DIN</Label><Input value={block?.director2_din || ""} onChange={(e) => setBlock({ ...block!, director2_din: e.target.value })} /></div>
          <div><Label>Designation</Label><Input value={block?.director2_designation || ""} onChange={(e) => setBlock({ ...block!, director2_designation: e.target.value })} /></div>
        </CardBody>
      </Card>

      {/* Company profile / disclosures (CIF + Forex) */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="font-medium text-navy">CIF imports + Forex</h3>
            <Button size="sm" onClick={saveProfile} disabled={busy}><Save className="h-4 w-4" />Save</Button>
          </div>
        </CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-3">
          <div><Label>CIF imports</Label><Input type="number" value={profile?.cif_imports ?? ""} onChange={(e) => setProfile({ ...profile!, cif_imports: Number(e.target.value), project_id: pid })} /></div>
          <div><Label>CIF components</Label><Input type="number" value={profile?.cif_components ?? ""} onChange={(e) => setProfile({ ...profile!, cif_components: Number(e.target.value), project_id: pid })} /></div>
          <div><Label>CIF capital goods</Label><Input type="number" value={profile?.cif_capital_goods ?? ""} onChange={(e) => setProfile({ ...profile!, cif_capital_goods: Number(e.target.value), project_id: pid })} /></div>
          <div><Label>FOB exports</Label><Input type="number" value={profile?.fob_exports ?? ""} onChange={(e) => setProfile({ ...profile!, fob_exports: Number(e.target.value), project_id: pid })} /></div>
          <div><Label>Forex earnings</Label><Input type="number" value={profile?.forex_earnings ?? ""} onChange={(e) => setProfile({ ...profile!, forex_earnings: Number(e.target.value), project_id: pid })} /></div>
          <div><Label>Forex expenditure</Label><Input type="number" value={profile?.forex_expenditure ?? ""} onChange={(e) => setProfile({ ...profile!, forex_expenditure: Number(e.target.value), project_id: pid })} /></div>
        </CardBody>
      </Card>

      {/* Other disclosures */}
      <Card>
        <CardHeader><h3 className="font-medium text-navy">Other Schedule III disclosures</h3></CardHeader>
        <CardBody className="!p-0">
          {disc && Object.keys(disc).length > 0 ? (
            <div className="divide-y divide-line">
              {Object.entries(disc).map(([ref, section]) => (
                <div key={ref} className="p-4">
                  <div className="font-medium text-navy">{ref}. {section.title}</div>
                  <div className="mt-3 space-y-2">
                    {section.items.map((it) => (
                      <div key={it.id} className="grid grid-cols-12 gap-2 items-center text-sm">
                        <div className="col-span-6 text-ink">{it.particulars}</div>
                        <div className="col-span-2"><Input type="number" placeholder="CY" defaultValue={it.cy ?? ""} onBlur={(e) => updDiscItem(it.id, "cy", Number(e.target.value))} /></div>
                        <div className="col-span-2"><Input type="number" placeholder="PY" defaultValue={it.py ?? ""} onBlur={(e) => updDiscItem(it.id, "py", Number(e.target.value))} /></div>
                        <div className="col-span-2"><Input placeholder="Notes" defaultValue={it.notes ?? ""} onBlur={(e) => updDiscItem(it.id, "notes", e.target.value)} /></div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-sm text-muted">No disclosure sections loaded.</div>
          )}
        </CardBody>
      </Card>
    </ProjectPageShell>
  );
}
