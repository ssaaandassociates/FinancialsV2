"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Plus, Building2, FolderOpen } from "lucide-react";

interface ClientRow {
  id: number;
  name: string;
  cin?: string;
  auditor_name?: string;
  project_count: number;
}

export default function DashboardPage() {
  const [clients, setClients] = useState<ClientRow[] | null>(null);
  const [err, setErr] = useState("");
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [cin, setCin] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setErr("");
      const data = await apiGet<ClientRow[]>("/clients/");
      setClients(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setErr(e instanceof ApiError ? `Failed to load clients (${e.status})` : "Failed to load clients");
      setClients([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await apiPost("/clients/", { name, cin: cin || undefined });
      setName("");
      setCin("");
      setAdding(false);
      load();
    } catch (e: any) {
      setErr(e.message || "Failed to create client");
    } finally {
      setBusy(false);
    }
  }

  const projectTotal = clients?.reduce((s, c) => s + c.project_count, 0) ?? 0;

  return (
    <div className="space-y-6 rise">
      {/* Title + create */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-navy">Your firm</h1>
          <p className="mt-1 text-sm text-muted">
            {clients ? `${clients.length} client${clients.length === 1 ? "" : "s"} · ${projectTotal} project${projectTotal === 1 ? "" : "s"}` : "Loading…"}
          </p>
        </div>
        <Button onClick={() => setAdding((v) => !v)} variant="gold">
          <Plus className="h-4 w-4" /> {adding ? "Cancel" : "New client"}
        </Button>
      </div>

      {/* Add form (inline, slides in) */}
      {adding && (
        <Card className="rise">
          <CardHeader>
            <h3 className="font-medium text-navy">Add a new client</h3>
          </CardHeader>
          <CardBody>
            <form onSubmit={create} className="grid gap-4 sm:grid-cols-[2fr_1fr_auto]">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted">Client name *</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="ABC Private Limited" required />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted">CIN</label>
                <Input value={cin} onChange={(e) => setCin(e.target.value)} placeholder="U12345MH2020PTC123456" />
              </div>
              <div className="flex items-end">
                <Button type="submit" disabled={busy || !name} className="w-full sm:w-auto">
                  {busy ? "Adding…" : "Add client"}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      )}

      {err && (
        <Card>
          <CardBody>
            <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>
          </CardBody>
        </Card>
      )}

      {/* Clients grid */}
      {clients === null ? (
        <Card><CardBody><div className="text-sm text-muted">Loading clients…</div></CardBody></Card>
      ) : clients.length === 0 ? (
        <Card>
          <CardBody className="py-12 text-center">
            <Building2 className="mx-auto h-10 w-10 text-muted" />
            <h3 className="mt-4 font-display text-xl font-semibold text-navy">No clients yet</h3>
            <p className="mt-1 text-sm text-muted">Add your first client to start preparing financials.</p>
            <Button onClick={() => setAdding(true)} variant="gold" className="mt-5">
              <Plus className="h-4 w-4" /> Add your first client
            </Button>
          </CardBody>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {clients.map((c) => (
            <Link key={c.id} href={`/client/${c.id}`} className="group">
              <Card className="h-full transition-shadow group-hover:shadow-md">
                <CardBody>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-display text-lg font-semibold text-navy group-hover:text-gold">
                        {c.name}
                      </div>
                      {c.cin && <div className="mt-0.5 font-mono text-xs text-muted">{c.cin}</div>}
                    </div>
                    <Badge tone={c.project_count > 0 ? "navy" : "neutral"}>
                      <FolderOpen className="mr-1 h-3 w-3" />
                      {c.project_count}
                    </Badge>
                  </div>
                  {c.auditor_name && (
                    <div className="mt-4 text-xs text-muted">
                      <span className="text-muted/70">Auditor: </span>
                      {c.auditor_name}
                    </div>
                  )}
                </CardBody>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
