"use client";
import { useState } from "react";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { clientApi, type ClientFull } from "@/lib/client-api";
import { Save, Edit3 } from "lucide-react";

export function OverviewTab({ client, onSaved }: { client: ClientFull; onSaved: () => void }) {
  const [editing, setEditing] = useState(false);
  const [f, setF] = useState<ClientFull>(client);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function up<K extends keyof ClientFull>(k: K, v: ClientFull[K]) { setF({ ...f, [k]: v }); }

  async function save() {
    setBusy(true); setErr("");
    try {
      // Strip server-only fields
      const { id, projects, ...payload } = f as any;
      await clientApi.update(client.id, payload);
      setEditing(false);
      onSaved();
    } catch (e: any) {
      setErr(e?.message || "Save failed");
    } finally { setBusy(false); }
  }

  function cancel() { setF(client); setEditing(false); setErr(""); }

  // Display-only read row helper
  const Row = ({ label, value }: { label: string; value?: string | number | null }) => (
    <div>
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-sm text-ink">{value ?? <span className="text-muted">—</span>}</div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl font-semibold text-navy">Company master data</h2>
        {!editing ? (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Edit3 className="h-4 w-4" /> Edit
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={cancel} disabled={busy}>Cancel</Button>
            <Button size="sm" onClick={save} disabled={busy}><Save className="h-4 w-4" />{busy ? "Saving…" : "Save"}</Button>
          </div>
        )}
      </div>

      {err && <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}

      <Card>
        <CardHeader><h3 className="font-medium text-navy">Identification</h3></CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {editing ? (<>
            <div><Label>Name *</Label><Input value={f.name || ""} onChange={(e) => up("name", e.target.value)} /></div>
            <div><Label>CIN</Label><Input value={f.cin || ""} onChange={(e) => up("cin", e.target.value)} /></div>
            <div><Label>PAN</Label><Input value={f.pan || ""} onChange={(e) => up("pan", e.target.value)} /></div>
            <div><Label>GSTIN</Label><Input value={f.gstin || ""} onChange={(e) => up("gstin", e.target.value)} /></div>
            <div><Label>Date of incorporation</Label><Input type="date" value={f.date_of_incorporation || ""} onChange={(e) => up("date_of_incorporation", e.target.value)} /></div>
            <div className="sm:col-span-2 lg:col-span-3"><Label>Registered office</Label><Textarea rows={2} value={f.registered_office || ""} onChange={(e) => up("registered_office", e.target.value)} /></div>
            <div className="sm:col-span-2 lg:col-span-3"><Label>Principal activity</Label><Input value={f.principal_activity || ""} onChange={(e) => up("principal_activity", e.target.value)} /></div>
          </>) : (<>
            <Row label="Name" value={f.name} />
            <Row label="CIN" value={f.cin} />
            <Row label="PAN" value={f.pan} />
            <Row label="GSTIN" value={f.gstin} />
            <Row label="Date of incorporation" value={f.date_of_incorporation} />
            <div className="sm:col-span-2 lg:col-span-3"><Row label="Registered office" value={f.registered_office} /></div>
            <div className="sm:col-span-2 lg:col-span-3"><Row label="Principal activity" value={f.principal_activity} /></div>
          </>)}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><h3 className="font-medium text-navy">Auditor</h3></CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-3">
          {editing ? (<>
            <div className="sm:col-span-3"><Label>Auditor name (firm)</Label><Input value={f.auditor_name || ""} onChange={(e) => up("auditor_name", e.target.value)} /></div>
            <div><Label>FRN</Label><Input value={f.auditor_frn || ""} onChange={(e) => up("auditor_frn", e.target.value)} /></div>
            <div><Label>Partner M. No.</Label><Input value={f.auditor_membership_no || ""} onChange={(e) => up("auditor_membership_no", e.target.value)} /></div>
          </>) : (<>
            <div className="sm:col-span-3"><Row label="Auditor name" value={f.auditor_name} /></div>
            <Row label="FRN" value={f.auditor_frn} />
            <Row label="Partner M. No." value={f.auditor_membership_no} />
          </>)}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><h3 className="font-medium text-navy">Share capital</h3></CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {editing ? (<>
            <div><Label>Face value (₹)</Label><Input type="number" value={f.face_value ?? 10} onChange={(e) => up("face_value", Number(e.target.value))} /></div>
            <div><Label>Authorised shares</Label><Input type="number" value={f.authorised_shares ?? 0} onChange={(e) => up("authorised_shares", Number(e.target.value))} /></div>
            <div><Label>Authorised capital</Label><Input type="number" value={f.authorised_capital ?? 0} onChange={(e) => up("authorised_capital", Number(e.target.value))} /></div>
            <div></div>
            <div><Label>Subscribed shares</Label><Input type="number" value={f.subscribed_shares ?? 0} onChange={(e) => up("subscribed_shares", Number(e.target.value))} /></div>
            <div><Label>Subscribed capital</Label><Input type="number" value={f.subscribed_capital ?? 0} onChange={(e) => up("subscribed_capital", Number(e.target.value))} /></div>
            <div><Label>Paid-up shares</Label><Input type="number" value={f.paidup_shares ?? 0} onChange={(e) => up("paidup_shares", Number(e.target.value))} /></div>
            <div><Label>Paid-up capital</Label><Input type="number" value={f.paidup_capital ?? 0} onChange={(e) => up("paidup_capital", Number(e.target.value))} /></div>
          </>) : (<>
            <Row label="Face value" value={f.face_value} />
            <Row label="Authorised shares" value={f.authorised_shares?.toLocaleString("en-IN")} />
            <Row label="Authorised capital" value={f.authorised_capital?.toLocaleString("en-IN")} />
            <div></div>
            <Row label="Subscribed shares" value={f.subscribed_shares?.toLocaleString("en-IN")} />
            <Row label="Subscribed capital" value={f.subscribed_capital?.toLocaleString("en-IN")} />
            <Row label="Paid-up shares" value={f.paidup_shares?.toLocaleString("en-IN")} />
            <Row label="Paid-up capital" value={f.paidup_capital?.toLocaleString("en-IN")} />
          </>)}
        </CardBody>
      </Card>
    </div>
  );
}
