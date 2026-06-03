"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { TopNav } from "@/components/top-nav";
import { Tabs, TabPanel } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, FileSpreadsheet, Trash2, Upload } from "lucide-react";
import { clientApi, directorsApi, shareholdersApi, policiesApi, customCoAApi, projectsApi, templatePaths, importMasterData, type ClientFull, type MasterImportResult } from "@/lib/client-api";
import { downloadFile } from "@/lib/api";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { FileDrop } from "@/components/ui/file-upload";

import { OverviewTab } from "./tabs/overview";
import { ProjectsTab } from "./tabs/projects";
import { DirectorsTab } from "./tabs/directors";
import { ShareholdersTab } from "./tabs/shareholders";
import { PoliciesTab } from "./tabs/policies";
import { CustomCoATab } from "./tabs/custom-coa";

const TAB_IDS = ["overview", "projects", "directors", "shareholders", "policies", "custom-coa"] as const;
type TabId = (typeof TAB_IDS)[number];

export default function ClientPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const clientId = Number(params.id);
  const { session, loading: authLoading } = useAuth();

  const [client, setClient] = useState<ClientFull | null>(null);
  const [loadError, setLoadError] = useState("");
  const [tab, setTab] = useState<TabId>("overview");

  // Counts shown next to tab labels
  const [counts, setCounts] = useState<Partial<Record<TabId, number>>>({});

  // Auth gate
  useEffect(() => {
    if (!authLoading && !session) router.replace("/login");
  }, [session, authLoading, router]);

  // Sync tab to URL hash (#projects etc)
  useEffect(() => {
    const fromHash = (typeof window !== "undefined" ? window.location.hash.replace("#", "") : "") as TabId;
    if (TAB_IDS.includes(fromHash)) setTab(fromHash);
  }, []);
  useEffect(() => {
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", `#${tab}`);
    }
  }, [tab]);

  // Load client
  async function reload() {
    try {
      setLoadError("");
      const c = await clientApi.get(clientId);
      setClient(c);
    } catch (e: any) {
      setLoadError(e?.status === 404 ? "Client not found." : "Could not load client.");
    }
  }

  // Load all counts (parallel)
  async function reloadCounts() {
    const [dirs, sh, pol, cc, prj] = await Promise.allSettled([
      directorsApi.list(clientId),
      shareholdersApi.list(clientId),
      policiesApi.list(clientId),
      customCoAApi.list(clientId),
      projectsApi.list(clientId),
    ]);
    setCounts({
      directors:     dirs.status === "fulfilled" ? dirs.value.length : 0,
      shareholders:  sh.status === "fulfilled" ? sh.value.length : 0,
      policies:      pol.status === "fulfilled" ? pol.value.length : 0,
      "custom-coa":  cc.status === "fulfilled" ? cc.value.length : 0,
      projects:      prj.status === "fulfilled" ? prj.value.length : 0,
    });
  }

  useEffect(() => {
    if (!clientId || !session) return;
    reload();
    reloadCounts();
  }, [clientId, session]);

  // Delete client
  const [delOpen, setDelOpen] = useState(false);
  const [delTyped, setDelTyped] = useState("");
  const [delBusy, setDelBusy] = useState(false);
  const [delErr, setDelErr] = useState("");

  // Master data import
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importBusy, setImportBusy] = useState(false);
  const [importResult, setImportResult] = useState<MasterImportResult | null>(null);
  const [importErr, setImportErr] = useState("");

  async function doImport() {
    if (!importFile || !client) return;
    setImportBusy(true); setImportErr(""); setImportResult(null);
    try {
      const r = await importMasterData(client.id, importFile);
      setImportResult(r);
      // Refresh everything
      reload(); reloadCounts();
    } catch (e: any) {
      setImportErr(e?.message || "Import failed");
    } finally { setImportBusy(false); }
  }

  async function doDelete() {
    if (!client) return;
    setDelBusy(true);
    setDelErr("");
    try {
      await clientApi.remove(client.id, delTyped);
      router.replace("/dashboard");
    } catch (e: any) {
      setDelErr(e?.message || "Delete failed.");
    } finally {
      setDelBusy(false);
    }
  }

  if (authLoading || !session) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted">Loading…</div>;
  }

  if (loadError) {
    return (
      <div className="min-h-screen">
        <TopNav />
        <main className="mx-auto max-w-7xl px-6 py-8">
          <Link href="/dashboard" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
            <ArrowLeft className="h-4 w-4" /> Back
          </Link>
          <div className="rounded-lg border border-line bg-white p-6 text-sm text-danger">{loadError}</div>
        </main>
      </div>
    );
  }

  if (!client) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted">Loading client…</div>;
  }

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Link href="/dashboard" className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
          <ArrowLeft className="h-4 w-4" /> All clients
        </Link>

        {/* Header */}
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold text-navy">{client.name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted">
              {client.cin && <span className="font-mono">{client.cin}</span>}
              {client.pan && <span className="font-mono">PAN {client.pan}</span>}
              {client.principal_activity && <Badge tone="navy">{client.principal_activity}</Badge>}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="md" onClick={() => { setImportOpen(true); setImportFile(null); setImportResult(null); setImportErr(""); }}>
              <Upload className="h-4 w-4" /> Import master data
            </Button>
            <button onClick={() => downloadFile(templatePaths.current(client.id)).catch((e) => alert("Download failed: " + (e?.message || e)))} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface">
              <Download className="h-4 w-4" /> Export master data
            </button>
            <button onClick={() => downloadFile(templatePaths.blank).catch((e) => alert("Download failed: " + (e?.message || e)))} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface">
              <FileSpreadsheet className="h-4 w-4" /> Blank template
            </button>
            <Button variant="ghost" size="sm" onClick={() => setDelOpen(true)} className="text-danger hover:bg-dangerpale">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Tabs
          value={tab}
          onChange={(v) => setTab(v as TabId)}
          tabs={[
            { id: "overview",     label: "Overview" },
            { id: "projects",     label: "Projects",     count: counts.projects },
            { id: "directors",    label: "Directors",    count: counts.directors },
            { id: "shareholders", label: "Shareholders", count: counts.shareholders },
            { id: "policies",     label: "Policies",     count: counts.policies },
            { id: "custom-coa",   label: "Custom CoA",   count: counts["custom-coa"] },
          ]}
        />

        <TabPanel when="overview" current={tab}>
          <OverviewTab client={client} onSaved={reload} />
        </TabPanel>
        <TabPanel when="projects" current={tab}>
          <ProjectsTab clientId={client.id} onChanged={reloadCounts} />
        </TabPanel>
        <TabPanel when="directors" current={tab}>
          <DirectorsTab clientId={client.id} onChanged={reloadCounts} />
        </TabPanel>
        <TabPanel when="shareholders" current={tab}>
          <ShareholdersTab clientId={client.id} onChanged={reloadCounts} />
        </TabPanel>
        <TabPanel when="policies" current={tab}>
          <PoliciesTab clientId={client.id} onChanged={reloadCounts} />
        </TabPanel>
        <TabPanel when="custom-coa" current={tab}>
          <CustomCoATab clientId={client.id} onChanged={reloadCounts} />
        </TabPanel>

        {/* Delete client dialog */}
        <Dialog
          open={delOpen}
          onClose={() => { setDelOpen(false); setDelTyped(""); setDelErr(""); }}
          title="Delete this client?"
          footer={
            <>
              <Button variant="outline" onClick={() => { setDelOpen(false); setDelTyped(""); setDelErr(""); }}>Cancel</Button>
              <Button variant="danger" disabled={delTyped.trim() !== client.name.trim() || delBusy} onClick={doDelete}>
                {delBusy ? "Deleting…" : "Permanently delete"}
              </Button>
            </>
          }
        >
          <div className="space-y-3 text-sm text-ink">
            <div className="rounded-lg bg-dangerpale px-3 py-2 text-danger">
              This permanently deletes <strong>{client.name}</strong>, all its projects, trial balances,
              mappings, audit entries, and supplementary records. This cannot be undone.
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted">
                Type the client name to confirm:
              </label>
              <Input
                value={delTyped}
                onChange={(e) => setDelTyped(e.target.value)}
                placeholder={client.name}
                autoComplete="off"
                spellCheck={false}
              />
            </div>
            {delErr && <div className="rounded-lg bg-dangerpale px-3 py-2 text-danger">{delErr}</div>}
          </div>
        </Dialog>
        {/* Master data import dialog */}
        <Dialog
          open={importOpen}
          onClose={() => { setImportOpen(false); setImportFile(null); setImportResult(null); setImportErr(""); }}
          title="Import master data"
          size="lg"
          footer={
            importResult ? (
              <Button onClick={() => { setImportOpen(false); setImportFile(null); setImportResult(null); }}>Done</Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => { setImportOpen(false); setImportFile(null); }}>Cancel</Button>
                <Button onClick={doImport} disabled={!importFile || importBusy}>
                  {importBusy ? "Importing…" : "Upload & import"}
                </Button>
              </>
            )
          }
        >
          {!importResult ? (
            <div className="space-y-3 text-sm">
              <div className="rounded-lg bg-navy-pale px-3 py-2 text-navy">
                Upload a filled blank template (or a modified export-current).
                Records are upserted by name — existing directors/shareholders/policies
                with matching names are <strong>updated</strong>, new ones are <strong>created</strong>.
              </div>
              <div className="rounded-lg bg-gold-light px-3 py-2 text-xs text-ink">
                <strong>Tip:</strong> if you're using the blank template, delete the sample rows
                before uploading — otherwise they will be imported as real records.
              </div>
              <FileDrop onFile={setImportFile} accept=".xlsx,.xlsm,.xls" disabled={importBusy} />
              {importErr && <div className="rounded-lg bg-dangerpale px-3 py-2 text-danger">{importErr}</div>}
            </div>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="rounded-lg bg-okpale px-3 py-2 text-ok">
                Import complete. Sheets processed: {importResult.sheets_processed.join(", ")}
              </div>
              <div className="grid grid-cols-2 gap-2">
                {importResult.client_master_fields_updated != null && (
                  <ImportStat label="Client master" value={`${importResult.client_master_fields_updated} field${importResult.client_master_fields_updated === 1 ? "" : "s"} updated`} />
                )}
                {importResult.directors && (
                  <ImportStat label="Directors" value={`${importResult.directors.created} new, ${importResult.directors.updated} updated`} />
                )}
                {importResult.shareholders && (
                  <ImportStat label="Shareholders" value={`${importResult.shareholders.created} new, ${importResult.shareholders.updated} updated`} />
                )}
                {importResult.custom_coa && (
                  <ImportStat label="Custom CoA" value={`${importResult.custom_coa.created} new, ${importResult.custom_coa.updated} updated`} />
                )}
                {importResult.policies && (
                  <ImportStat label="Policies" value={`${importResult.policies.created} new, ${importResult.policies.updated} updated`} />
                )}
              </div>
              {importResult.warnings.length > 0 && (
                <div className="rounded-lg bg-dangerpale px-3 py-2 text-danger">
                  <div className="font-medium">Warnings:</div>
                  <ul className="ml-4 list-disc">
                    {importResult.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Dialog>
      </main>
    </div>
  );
}

function ImportStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-0.5 text-sm font-medium text-navy">{value}</div>
    </div>
  );
}
