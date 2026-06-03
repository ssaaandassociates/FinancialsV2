"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ProjectPageShell } from "@/components/project-shell";
import { useAuthGuard } from "@/lib/use-auth-guard";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Empty } from "@/components/ui/empty";
import { Save, Package, FileSpreadsheet, Upload, Download } from "lucide-react";
import { stockApi, ppeApi, ppeTemplate, type ClosingStockRow, type PPEEntry } from "@/lib/project-api";
import { downloadFile } from "@/lib/api";
import { Dialog } from "@/components/ui/dialog";
import { FileDrop } from "@/components/ui/file-upload";

export default function StockPPEPage() {
  const params = useParams<{ id: string }>();
  const pid = Number(params.id);
  const { session, loading } = useAuthGuard();
  const [stock, setStock] = useState<ClosingStockRow[]>([]);
  const [ppe, setPpe] = useState<PPEEntry[] | null>(null);
  const [stockTypes, setStockTypes] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  // PPE import
  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importBusy, setImportBusy] = useState(false);
  const [importResult, setImportResult] = useState<{ created: number; updated: number } | null>(null);
  const [importErr, setImportErr] = useState("");

  async function doImportPPE() {
    if (!importFile) return;
    setImportBusy(true); setImportErr(""); setImportResult(null);
    try {
      const r = await ppeTemplate.import(pid, importFile);
      setImportResult(r);
      // Refresh PPE list
      const fresh = await ppeApi.list(pid);
      setPpe(Array.isArray(fresh) ? fresh : []);
    } catch (e: any) {
      setImportErr(e?.message || "PPE import failed");
    } finally { setImportBusy(false); }
  }

  async function reload() {
    try {
      setErr("");
      const [s, p, t] = await Promise.all([stockApi.list(pid), ppeApi.list(pid), stockApi.types(pid).catch(() => [])]);
      setStock(Array.isArray(s) ? s : []); setPpe(Array.isArray(p) ? p : []); setStockTypes(Array.isArray(t) ? t : []);
    } catch (e: any) { setErr(e?.message || "Failed to load"); }
  }
  useEffect(() => { if (session) reload(); }, [session, pid]);

  function updStock(type: string, field: "cy_amount" | "py_amount", v: number) {
    setStock((prev) => {
      const found = prev.find((r) => r.stock_type === type);
      if (found) return prev.map((r) => r.stock_type === type ? { ...r, [field]: v } : r);
      return [...prev, { project_id: pid, stock_type: type, [field]: v } as ClosingStockRow];
    });
  }

  async function saveStock() {
    setBusy(true); setErr(""); setMsg("");
    try {
      for (const row of stock) await stockApi.save(row);
      setMsg("Stock saved."); setTimeout(() => setMsg(""), 2500);
    } catch (e: any) { setErr(e?.message || "Save failed"); }
    finally { setBusy(false); }
  }

  async function savePPE(e: PPEEntry) {
    const { id, project_id, coa_code, particulars, ...rest } = e;
    await ppeApi.update(id, rest);
  }
  function updPPE(id: number, field: keyof PPEEntry, v: number) {
    setPpe((prev) => prev ? prev.map((r) => r.id === id ? { ...r, [field]: v } : r) : prev);
  }
  async function saveAllPPE() {
    if (!ppe) return;
    setBusy(true); setMsg("");
    try { for (const r of ppe) await savePPE(r); setMsg("PPE saved."); setTimeout(() => setMsg(""), 2500); }
    catch (e: any) { setErr(e?.message || "PPE save failed"); }
    finally { setBusy(false); }
  }

  if (loading || !session) return null;

  const types = stockTypes.length ? stockTypes : ["Raw Materials", "Work in Progress", "Finished Goods", "Stores & Spares", "Stock in Trade"];

  return (
    <ProjectPageShell projectId={pid} title="Closing stock & PPE">
      {err && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>}
      {msg && <div className="mb-4 rounded-lg bg-okpale px-3 py-2 text-sm text-ok">{msg}</div>}

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="font-medium text-navy"><Package className="inline h-4 w-4 mr-1.5 -mt-0.5" />Closing stock</h3>
            <Button size="sm" onClick={saveStock} disabled={busy}><Save className="h-4 w-4" />Save stock</Button>
          </div>
        </CardHeader>
        <CardBody className="!p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                <th className="px-4 py-3">Stock type</th>
                <th className="px-4 py-3 text-right">CY amount</th>
                <th className="px-4 py-3 text-right">PY amount</th>
              </tr>
            </thead>
            <tbody>
              {types.map((t) => {
                const r = stock.find((s) => s.stock_type === t) || ({} as ClosingStockRow);
                return (
                  <tr key={t} className="border-b border-line last:border-0">
                    <td className="px-4 py-3 font-medium text-ink">{t}</td>
                    <td className="px-4 py-3 text-right"><Input type="number" value={r.cy_amount ?? ""} onChange={(e) => updStock(t, "cy_amount", Number(e.target.value))} className="!text-right" /></td>
                    <td className="px-4 py-3 text-right"><Input type="number" value={r.py_amount ?? ""} onChange={(e) => updStock(t, "py_amount", Number(e.target.value))} className="!text-right" /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <h3 className="font-medium text-navy"><FileSpreadsheet className="inline h-4 w-4 mr-1.5 -mt-0.5" />PPE schedule</h3>
            <div className="flex gap-2">
              <button onClick={() => downloadFile(ppeTemplate.downloadPath).catch((e) => alert("Download failed: " + (e?.message || e)))} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs font-medium hover:bg-surface">
                <Download className="h-3.5 w-3.5" /> Template
              </button>
              <Button size="sm" variant="outline" onClick={() => { setImportOpen(true); setImportFile(null); setImportResult(null); setImportErr(""); }}>
                <Upload className="h-4 w-4" /> Import PPE
              </Button>
              {ppe && ppe.length > 0 && <Button size="sm" onClick={saveAllPPE} disabled={busy}><Save className="h-4 w-4" />Save all PPE</Button>}
            </div>
          </div>
        </CardHeader>
        <CardBody className="!p-0 overflow-x-auto">
          {ppe === null ? <div className="p-4 text-sm text-muted">Loading…</div>
            : ppe.length === 0 ? <div className="p-6"><Empty icon={<FileSpreadsheet className="h-6 w-6" />} title="No PPE rows yet" hint="PPE rows auto-seed when you map ledgers to BS-AS-01-* codes." /></div>
            : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-line bg-surface/50 text-left font-medium uppercase tracking-wide text-muted">
                    <th className="px-3 py-2.5">Asset class</th>
                    <th className="px-3 py-2.5 text-right">Gross open CY</th>
                    <th className="px-3 py-2.5 text-right">Add CY</th>
                    <th className="px-3 py-2.5 text-right">Disp CY</th>
                    <th className="px-3 py-2.5 text-right">Dep open CY</th>
                    <th className="px-3 py-2.5 text-right">Dep yr CY</th>
                    <th className="px-3 py-2.5 text-right">Dep disp CY</th>
                    <th className="px-3 py-2.5 text-right">Gross open PY</th>
                    <th className="px-3 py-2.5 text-right">Add PY</th>
                    <th className="px-3 py-2.5 text-right">Disp PY</th>
                    <th className="px-3 py-2.5 text-right">Dep open PY</th>
                    <th className="px-3 py-2.5 text-right">Dep yr PY</th>
                    <th className="px-3 py-2.5 text-right">Dep disp PY</th>
                  </tr>
                </thead>
                <tbody>
                  {ppe.map((e) => (
                    <tr key={e.id} className="border-b border-line last:border-0">
                      <td className="px-3 py-2 font-medium text-ink whitespace-nowrap">{e.particulars}<div className="font-mono text-[10px] text-muted">{e.coa_code}</div></td>
                      {(["gross_opening_cy","gross_additions_cy","gross_disposals_cy","dep_opening_cy","dep_for_year_cy","dep_on_disposals_cy","gross_opening_py","gross_additions_py","gross_disposals_py","dep_opening_py","dep_for_year_py","dep_on_disposals_py"] as const).map((f) => (
                        <td key={f} className="px-1 py-1.5 text-right">
                          <Input type="number" value={(e as any)[f] ?? ""} onChange={(ev) => updPPE(e.id, f, Number(ev.target.value))} className="!h-7 !text-xs !text-right !w-24" />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
        </CardBody>
      </Card>

      {/* PPE import dialog */}
      <Dialog
        open={importOpen}
        onClose={() => { setImportOpen(false); setImportFile(null); setImportResult(null); setImportErr(""); }}
        title="Import PPE schedule"
        footer={
          importResult ? (
            <Button onClick={() => { setImportOpen(false); setImportFile(null); setImportResult(null); }}>Done</Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => { setImportOpen(false); setImportFile(null); }}>Cancel</Button>
              <Button onClick={doImportPPE} disabled={!importFile || importBusy}>
                {importBusy ? "Importing…" : "Upload & import"}
              </Button>
            </>
          )
        }
      >
        {!importResult ? (
          <div className="space-y-3 text-sm">
            <div className="rounded-lg bg-navy-pale px-3 py-2 text-navy">
              Upload a filled PPE template. Rows are matched by <strong>CoA code</strong>: existing
              codes are updated, missing ones are created. Download a fresh template first if you
              don't have one.
            </div>
            <FileDrop onFile={setImportFile} accept=".xlsx,.xlsm,.xls" disabled={importBusy} />
            {importErr && <div className="rounded-lg bg-dangerpale px-3 py-2 text-danger">{importErr}</div>}
          </div>
        ) : (
          <div className="rounded-lg bg-okpale px-3 py-2 text-sm text-ok">
            Imported successfully: <strong>{importResult.updated}</strong> row{importResult.updated === 1 ? "" : "s"} updated,
            <strong> {importResult.created}</strong> row{importResult.created === 1 ? "" : "s"} created.
          </div>
        )}
      </Dialog>
    </ProjectPageShell>
  );
}
