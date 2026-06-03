"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { TopNav } from "@/components/top-nav";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Empty } from "@/components/ui/empty";
import { Dialog } from "@/components/ui/dialog";
import { FileDrop } from "@/components/ui/file-upload";
import { Combobox, type ComboOption } from "@/components/ui/combobox";
import {
  ArrowLeft, Upload, Wand2, Search, X, Save, Check,
  AlertCircle, RefreshCw, Download, FileDown, FileUp, Copy as CopyIcon,
  History, ChevronRight, Loader2
} from "lucide-react";
import {
  tbApi, mappingApi, exportUrls,
  type TBRow, type CoACode, type AutoMapResult, type PrevProjectOpt,
} from "@/lib/mapping-api";
import { cn } from "@/lib/utils";

type StatusFilter = "all" | "unmapped" | "mapped" | "custom";

// Cosmetic only: how long to wait after the last edit before persisting
const AUTOSAVE_MS = 2000;

export default function MappingPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const projectId = Number(params.id);
  const { session, loading: authLoading } = useAuth();

  // Auth gate
  useEffect(() => {
    if (!authLoading && !session) router.replace("/login");
  }, [session, authLoading, router]);

  const [rows, setRows] = useState<TBRow[] | null>(null);
  const [coa, setCoa] = useState<CoACode[]>([]);
  const [pageError, setPageError] = useState("");

  // Filter state
  const [statusF, setStatusF] = useState<StatusFilter>("all");
  const [groupF, setGroupF] = useState<string>("");
  const [searchF, setSearchF] = useState("");

  // Track unsaved/saving/saved rows for the indicator
  type SaveState = "saved" | "dirty" | "saving" | "error";
  const [saveState, setSaveState] = useState<Record<number, SaveState>>({});
  // Pending changes queued for auto-save
  const pendingRef = useRef<Map<number, string>>(new Map());
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Action dialogs
  const [showUpload, setShowUpload] = useState(false);
  const [showImportMapped, setShowImportMapped] = useState(false);
  const [showImportPrev, setShowImportPrev] = useState(false);
  const [showCopy, setShowCopy] = useState<TBRow | null>(null);
  const [showAutoMapResult, setShowAutoMapResult] = useState<AutoMapResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionMsg, setActionMsg] = useState("");

  // ---------- Data loading ----------
  async function reloadAll() {
    setPageError("");
    try {
      const [tb, codes] = await Promise.all([
        tbApi.list(projectId),
        mappingApi.listCoA(),
      ]);
      setRows(tb);
      setCoa(codes);
    } catch (e: any) {
      setPageError(e?.message || "Failed to load mapping data");
      setRows([]);
    }
  }
  useEffect(() => { if (session && projectId) reloadAll(); }, [session, projectId]);

  // ---------- CoA derivations (frontend logic mirrors the backend fix) ----------
  // Majors = codes that are anyone's parent
  // Subs = codes that aren't majors themselves, parent_code chain leading to a major
  const majors: ComboOption[] = useMemo(() => {
    const parentSet = new Set<string>();
    coa.forEach((c) => { if (c.tally_group) parentSet.add(c.tally_group); });
    // Use schedule_ref as the "parent code" semantically — backend stores it as parent_code on the
    // server-side query. But here, since /coa/ doesn't return parent_code directly, we use the
    // server's existing logic via fs_type + level. Simplest accurate proxy: any code at level 2 or 3.
    const seenParents = new Set<string>();
    coa.forEach((c) => {
      // crude: if a code with longer prefix exists, this one is a parent
      const childExists = coa.some(
        (x) => x.code !== c.code && x.code.startsWith(c.code + "-")
      );
      if (childExists) seenParents.add(c.code);
    });
    return coa
      .filter((c) => seenParents.has(c.code))
      .map((c) => ({ value: c.code, label: c.particulars }));
  }, [coa]);

  // sub→major map: walk up the code chain (by stripping -XX suffixes) until we find a major
  const subToMajor = useMemo(() => {
    const m: Record<string, string> = {};
    const codeSet = new Set(coa.map((c) => c.code));
    const majorSet = new Set(majors.map((m) => m.value));
    coa.forEach((c) => {
      if (majorSet.has(c.code)) return;
      // strip "-NN" suffixes until we find a major in the set
      let cur = c.code;
      while (cur.includes("-")) {
        const trimmed = cur.substring(0, cur.lastIndexOf("-"));
        if (majorSet.has(trimmed)) { m[c.code] = trimmed; return; }
        if (!codeSet.has(trimmed)) { cur = trimmed; continue; }
        cur = trimmed;
      }
    });
    return m;
  }, [coa, majors]);

  // For each major, the list of sub-codes
  const subsByMajor = useMemo(() => {
    const m: Record<string, ComboOption[]> = {};
    coa.forEach((c) => {
      const maj = subToMajor[c.code];
      if (!maj) return;
      (m[maj] = m[maj] || []).push({ value: c.code, label: c.particulars });
    });
    Object.values(m).forEach((arr) => arr.sort((a, b) => a.value.localeCompare(b.value)));
    return m;
  }, [coa, subToMajor]);

  // ---------- Filter logic ----------
  const groupOptions = useMemo(() => {
    if (!rows) return [];
    return Array.from(new Set(rows.map((r) => r.tally_group).filter(Boolean))).sort() as string[];
  }, [rows]);

  // For "Custom CoA" filter we need to know which codes are custom (not in standard CoA)
  const standardCodes = useMemo(() => new Set(coa.map((c) => c.code)), [coa]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const q = searchF.trim().toLowerCase();
    return rows.filter((r) => {
      // status
      const isMapped = !!r.coa_code;
      const isCustom = isMapped && !standardCodes.has(r.coa_code!);
      if (statusF === "mapped" && !isMapped) return false;
      if (statusF === "unmapped" && isMapped) return false;
      if (statusF === "custom" && !isCustom) return false;
      // group
      if (groupF && r.tally_group !== groupF) return false;
      // search
      if (q && !(r.ledger_name.toLowerCase().includes(q) || (r.tally_group || "").toLowerCase().includes(q))) return false;
      return true;
    });
  }, [rows, statusF, groupF, searchF, standardCodes]);

  const counts = useMemo(() => {
    if (!rows) return { all: 0, mapped: 0, unmapped: 0, custom: 0 };
    let mapped = 0, unmapped = 0, custom = 0;
    rows.forEach((r) => {
      if (r.coa_code) {
        mapped++;
        if (!standardCodes.has(r.coa_code)) custom++;
      } else unmapped++;
    });
    return { all: rows.length, mapped, unmapped, custom };
  }, [rows, standardCodes]);

  // ---------- Mapping edits (with debounced auto-save) ----------
  function localUpdate(id: number, coaCode: string) {
    setRows((prev) => prev ? prev.map((r) => r.id === id ? { ...r, coa_code: coaCode || null } : r) : prev);
    setSaveState((prev) => ({ ...prev, [id]: "dirty" }));
    pendingRef.current.set(id, coaCode);
    // restart debounce
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(flushPending, AUTOSAVE_MS);
  }

  async function flushPending() {
    if (pendingRef.current.size === 0) return;
    const batch = Array.from(pendingRef.current.entries()).map(([tb_row_id, coa_code]) => ({ tb_row_id, coa_code }));
    const ids = batch.map((b) => b.tb_row_id);
    pendingRef.current.clear();
    setSaveState((prev) => { const n = { ...prev }; ids.forEach((id) => n[id] = "saving"); return n; });
    try {
      await mappingApi.saveBatch(batch);
      setSaveState((prev) => { const n = { ...prev }; ids.forEach((id) => n[id] = "saved"); return n; });
      // Clear "saved" indicator after 1.5s
      setTimeout(() => setSaveState((prev) => {
        const n = { ...prev };
        ids.forEach((id) => { if (n[id] === "saved") delete n[id]; });
        return n;
      }), 1500);
    } catch (e: any) {
      setSaveState((prev) => { const n = { ...prev }; ids.forEach((id) => n[id] = "error"); return n; });
    }
  }

  async function saveAllNow() {
    if (timerRef.current) clearTimeout(timerRef.current);
    await flushPending();
  }

  // ---------- Bulk actions ----------
  async function runAutoMap(force: boolean) {
    setBusy(true); setActionMsg("");
    try {
      const result = await mappingApi.autoMap(projectId, force);
      setShowAutoMapResult(result);
      await reloadAll();
    } catch (e: any) {
      setActionMsg(e?.message || "Auto-map failed");
    } finally { setBusy(false); }
  }

  async function handleUpload(file: File) {
    setBusy(true); setActionMsg("");
    try {
      const result = await tbApi.upload(projectId, file);
      setActionMsg(`Imported ${result.rows_imported ?? "?"} rows.`);
      setShowUpload(false);
      await reloadAll();
    } catch (e: any) {
      setActionMsg("Upload failed: " + (e?.message || "unknown error"));
    } finally { setBusy(false); }
  }

  async function handleImportMapped(file: File) {
    setBusy(true); setActionMsg("");
    try {
      const result = await tbApi.importMappedTB(projectId, file);
      setActionMsg(`Imported ${result.rows_imported ?? "?"} rows with mappings.`);
      setShowImportMapped(false);
      await reloadAll();
    } catch (e: any) {
      setActionMsg("Import failed: " + (e?.message || "unknown error"));
    } finally { setBusy(false); }
  }

  // ---------- Save status indicator ----------
  const dirtyCount = Object.values(saveState).filter((s) => s === "dirty" || s === "saving").length;
  const errorCount = Object.values(saveState).filter((s) => s === "error").length;

  // Save unsaved on tab close / route change
  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (pendingRef.current.size > 0) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", onBeforeUnload);
      // Flush any pending on unmount
      if (pendingRef.current.size > 0) flushPending();
    };
  }, []);

  if (authLoading || !session) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-muted">Loading…</div>;
  }

  return (
    <div className="min-h-screen pb-12">
      <TopNav />

      {/* Sticky save bar */}
      <div className="sticky top-16 z-20 border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-2.5">
          <div className="flex items-center gap-3 text-sm">
            <Link href={`/project/${projectId}`} className="inline-flex items-center gap-1 text-muted hover:text-ink">
              <ArrowLeft className="h-4 w-4" /> Project
            </Link>
            <span className="text-muted">·</span>
            <span className="font-medium text-navy">Upload & Mapping</span>
          </div>
          <div className="flex items-center gap-2">
            <SaveIndicator dirtyCount={dirtyCount} errorCount={errorCount} />
            <Button size="sm" variant="primary" onClick={saveAllNow} disabled={dirtyCount === 0 && errorCount === 0}>
              <Save className="h-4 w-4" /> Save all
            </Button>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-6 py-6">
        {pageError && <div className="mb-4 rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{pageError}</div>}
        {actionMsg && <div className="mb-4 rounded-lg bg-okpale px-3 py-2 text-sm text-ok">{actionMsg}</div>}

        {/* Action toolbar */}
        <Card className="mb-4">
          <CardBody className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => setShowUpload(true)}><Upload className="h-4 w-4" /> Upload TB</Button>
              <Button variant="outline" onClick={() => runAutoMap(false)} disabled={busy || !rows?.length}>
                <Wand2 className="h-4 w-4" /> Auto-map
              </Button>
              <Button variant="outline" onClick={() => setShowImportPrev(true)} disabled={!rows?.length}>
                <History className="h-4 w-4" /> Import from prev FY
              </Button>
              <Button variant="outline" onClick={() => setShowImportMapped(true)}>
                <FileUp className="h-4 w-4" /> Import mapped TB
              </Button>
            </div>
            <div className="flex gap-2">
              <a href={exportUrls.tbTemplate} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface">
                <FileDown className="h-4 w-4" /> TB template
              </a>
              {rows && rows.length > 0 && (
                <a href={exportUrls.mappedTB(projectId)} className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-surface">
                  <Download className="h-4 w-4" /> Export
                </a>
              )}
            </div>
          </CardBody>
        </Card>

        {rows && rows.length === 0 ? (
          <Empty
            icon={<Upload className="h-6 w-6" />}
            title="No trial balance uploaded yet"
            hint="Upload your Tally TB to begin mapping. The auto-mapper will try 31 keyword rules."
            action={<Button variant="gold" onClick={() => setShowUpload(true)}><Upload className="h-4 w-4" /> Upload TB</Button>}
          />
        ) : (
          <>
            {/* Unified filter bar */}
            <Card className="mb-4">
              <CardBody className="flex flex-wrap items-center gap-3">
                <PillFilter label={`All (${counts.all})`} active={statusF === "all"} onClick={() => setStatusF("all")} />
                <PillFilter label={`Unmapped (${counts.unmapped})`} active={statusF === "unmapped"} onClick={() => setStatusF("unmapped")} tone="danger" />
                <PillFilter label={`Mapped (${counts.mapped})`} active={statusF === "mapped"} onClick={() => setStatusF("mapped")} tone="ok" />
                <PillFilter label={`Custom CoA (${counts.custom})`} active={statusF === "custom"} onClick={() => setStatusF("custom")} tone="gold" />

                <div className="h-6 w-px bg-line" />

                <Select value={groupF} onChange={(e) => setGroupF(e.target.value)} className="max-w-[200px]">
                  <option value="">All groups</option>
                  {groupOptions.map((g) => <option key={g} value={g}>{g}</option>)}
                </Select>

                <div className="relative flex-1 min-w-[200px]">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                  <Input value={searchF} onChange={(e) => setSearchF(e.target.value)} placeholder="Search ledger or group…" className="pl-9" />
                </div>

                <Badge tone="navy">{filtered.length} shown</Badge>

                {(statusF !== "all" || groupF || searchF) && (
                  <Button size="sm" variant="ghost" onClick={() => { setStatusF("all"); setGroupF(""); setSearchF(""); }}>
                    <X className="h-3 w-3" /> Clear
                  </Button>
                )}
              </CardBody>
            </Card>

            {/* Mapping grid */}
            <Card>
              <CardBody className="!p-0 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-line bg-surface/50 text-left text-xs font-medium uppercase tracking-wide text-muted">
                      <th className="px-4 py-3 w-12">#</th>
                      <th className="px-4 py-3">Ledger</th>
                      <th className="px-4 py-3">Group</th>
                      <th className="px-4 py-3 text-right">CY Net</th>
                      <th className="px-4 py-3 w-[180px]">Major code</th>
                      <th className="px-4 py-3 w-[300px]">Sub-code</th>
                      <th className="px-4 py-3 w-[40px]"></th>
                      <th className="px-4 py-3 w-[40px]"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((r, i) => {
                      const currentMajor = r.coa_code ? subToMajor[r.coa_code] || (majors.some((m) => m.value === r.coa_code) ? r.coa_code : "") : "";
                      const subs = currentMajor ? (subsByMajor[currentMajor] || []) : [];
                      // Allow custom CoA (or codes whose major can't be resolved) to still appear as sub
                      const showCurrentAsSubOption =
                        r.coa_code && currentMajor && !subs.some((s) => s.value === r.coa_code);
                      const subOptions: ComboOption[] = showCurrentAsSubOption
                        ? [{ value: r.coa_code!, label: "(custom)" }, ...subs]
                        : subs;
                      const status = saveState[r.id];
                      return (
                        <tr key={r.id} className={cn("border-b border-line last:border-0 align-top",
                          !r.coa_code && "bg-dangerpale/30")}>
                          <td className="px-4 py-3 text-xs text-muted">{i + 1}</td>
                          <td className="px-4 py-3">
                            <div className="font-medium text-ink">{r.ledger_name}</div>
                          </td>
                          <td className="px-4 py-3 text-xs text-muted">{r.tally_group || "—"}</td>
                          <td className="px-4 py-3 text-right font-mono tabular-nums">
                            {fmtINR(r.cy_net)}
                          </td>
                          <td className="px-4 py-3">
                            <Combobox
                              value={currentMajor}
                              onChange={(v) => {
                                // Changing the major clears the sub
                                if (v !== currentMajor) localUpdate(r.id, v);
                              }}
                              options={majors}
                              size="sm"
                              placeholder="-- Major --"
                              showValueInTrigger={false}
                            />
                          </td>
                          <td className="px-4 py-3">
                            <Combobox
                              value={r.coa_code || ""}
                              onChange={(v) => localUpdate(r.id, v)}
                              options={subOptions}
                              size="sm"
                              placeholder={currentMajor ? "-- Sub --" : "Pick major first"}
                              disabled={!currentMajor}
                              emptyText={currentMajor ? "No sub-codes" : "Pick major first"}
                            />
                          </td>
                          <td className="px-4 py-3">
                            <RowStatusDot status={status} mapped={!!r.coa_code} />
                          </td>
                          <td className="px-4 py-3">
                            <button
                              onClick={() => setShowCopy(r)}
                              disabled={!r.coa_code}
                              title="Copy this mapping to other rows"
                              className="rounded p-1 text-muted hover:bg-surface hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                              <CopyIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-4 py-8 text-center text-sm text-muted">
                          No rows match the current filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardBody>
            </Card>
          </>
        )}

        {/* === Dialogs === */}
        <UploadDialog open={showUpload} onClose={() => setShowUpload(false)} onUpload={handleUpload} busy={busy} title="Upload Trial Balance" hint="Excel/CSV with columns: Ledger, Tally Group, CY Debit, CY Credit, PY Debit, PY Credit" />
        <UploadDialog open={showImportMapped} onClose={() => setShowImportMapped(false)} onUpload={handleImportMapped} busy={busy} title="Import Mapped TB" hint="Excel with columns: Ledger, CoA Code (and optional balances)" />

        <Dialog
          open={!!showAutoMapResult}
          onClose={() => setShowAutoMapResult(null)}
          title="Auto-map complete"
          footer={
            <div className="flex w-full items-center justify-between gap-2">
              <Button variant="outline" onClick={() => { setShowAutoMapResult(null); runAutoMap(true); }} disabled={busy}>
                <RefreshCw className="h-4 w-4" /> Re-run (overwrite)
              </Button>
              <Button onClick={() => setShowAutoMapResult(null)}>Done</Button>
            </div>
          }
        >
          {showAutoMapResult && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Stat label="Total rows" value={showAutoMapResult.total_rows} />
              <Stat label="Mapped by keyword" value={showAutoMapResult.mapped_by_keyword} tone="ok" />
              <Stat label="Mapped by group" value={showAutoMapResult.mapped_by_tally_group} tone="ok" />
              <Stat label="Unmapped" value={showAutoMapResult.unmapped} tone={showAutoMapResult.unmapped > 0 ? "danger" : "neutral"} />
              <Stat label="Low confidence (review)" value={showAutoMapResult.low_confidence} tone="gold" />
            </div>
          )}
        </Dialog>

        <ImportPrevDialog open={showImportPrev} onClose={() => setShowImportPrev(false)} projectId={projectId} onDone={reloadAll} />

        <CopyMappingDialog
          source={showCopy}
          allRows={rows || []}
          onClose={() => setShowCopy(null)}
          onDone={reloadAll}
        />
      </main>
    </div>
  );
}

// ----------- Sub-components -----------

function PillFilter({ label, active, onClick, tone = "neutral" }: { label: string; active: boolean; onClick: () => void; tone?: "neutral" | "ok" | "danger" | "gold" }) {
  const tones = {
    neutral: active ? "bg-navy text-white" : "bg-white text-ink hover:bg-surface",
    ok:      active ? "bg-ok text-white"   : "bg-okpale text-ok hover:bg-okpale/70",
    danger:  active ? "bg-danger text-white" : "bg-dangerpale text-danger hover:bg-dangerpale/70",
    gold:    active ? "bg-gold text-white" : "bg-gold-light text-gold hover:bg-gold-light/70",
  } as const;
  return (
    <button
      onClick={onClick}
      className={cn("rounded-full border border-line px-3 py-1 text-xs font-medium transition-colors", tones[tone])}
    >{label}</button>
  );
}

function SaveIndicator({ dirtyCount, errorCount }: { dirtyCount: number; errorCount: number }) {
  if (errorCount > 0) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-danger">
        <AlertCircle className="h-4 w-4" /> {errorCount} failed
      </span>
    );
  }
  if (dirtyCount > 0) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-gold">
        <Loader2 className="h-4 w-4 animate-spin" /> Saving {dirtyCount}…
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ok">
      <Check className="h-4 w-4" /> All changes saved
    </span>
  );
}

function RowStatusDot({ status, mapped }: { status?: "saved" | "dirty" | "saving" | "error"; mapped: boolean }) {
  if (status === "saving") return <Loader2 className="h-4 w-4 animate-spin text-gold" />;
  if (status === "error")  return <AlertCircle className="h-4 w-4 text-danger" />;
  if (status === "saved")  return <Check className="h-4 w-4 text-ok" />;
  if (status === "dirty")  return <span className="block h-2 w-2 rounded-full bg-gold" />;
  if (!mapped)             return <span className="block h-2 w-2 rounded-full bg-danger" />;
  return <span className="block h-2 w-2 rounded-full bg-ok/40" />;
}

function Stat({ label, value, tone = "neutral" }: { label: string; value: number; tone?: "ok" | "danger" | "gold" | "neutral" }) {
  const tones = { ok: "text-ok", danger: "text-danger", gold: "text-gold", neutral: "text-navy" };
  return (
    <div className="rounded-lg border border-line p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className={cn("mt-1 text-2xl font-semibold", tones[tone])}>{value}</div>
    </div>
  );
}

function UploadDialog({ open, onClose, onUpload, busy, title, hint }: { open: boolean; onClose: () => void; onUpload: (f: File) => void; busy: boolean; title: string; hint: string; }) {
  const [file, setFile] = useState<File | null>(null);
  useEffect(() => { if (!open) setFile(null); }, [open]);
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={title}
      footer={
        <>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => file && onUpload(file)} disabled={!file || busy}>
            {busy ? "Uploading…" : "Upload"}
          </Button>
        </>
      }
    >
      <FileDrop onFile={setFile} hint={hint} disabled={busy} />
    </Dialog>
  );
}

function ImportPrevDialog({ open, onClose, projectId, onDone }: { open: boolean; onClose: () => void; projectId: number; onDone: () => void }) {
  const [prev, setPrev] = useState<PrevProjectOpt[] | null>(null);
  const [sel, setSel] = useState<number | "">("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!open) return;
    setMsg(""); setSel("");
    mappingApi.listPrevProjects(projectId).then(setPrev).catch(() => setPrev([]));
  }, [open, projectId]);

  async function doImport() {
    if (sel === "") return;
    setBusy(true); setMsg("");
    try {
      const r = await mappingApi.importPrev(Number(sel), projectId);
      setMsg(`Matched ${r.matched} ledgers from FY ${r.source_fy} (${r.skipped} new).`);
      onDone();
    } catch (e: any) { setMsg(e?.message || "Import failed"); }
    finally { setBusy(false); }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Import mapping from previous FY"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button onClick={doImport} disabled={sel === "" || busy}><ChevronRight className="h-4 w-4" />{busy ? "Importing…" : "Import"}</Button>
        </>
      }
    >
      <div className="space-y-3 text-sm">
        <p className="text-muted">Pick a previous FY for the same client. Ledgers matching by name will get their CoA codes copied across.</p>
        {prev === null ? (
          <div className="text-muted">Loading…</div>
        ) : prev.length === 0 ? (
          <div className="rounded-lg bg-surface px-3 py-2 text-muted">No previous projects with mappings found.</div>
        ) : (
          <Select value={sel} onChange={(e) => setSel(e.target.value === "" ? "" : Number(e.target.value))}>
            <option value="">— Select previous FY —</option>
            {prev.map((p) => (
              <option key={p.id} value={p.id}>FY {p.financial_year} ({p.mapping_count} mappings, {p.status})</option>
            ))}
          </Select>
        )}
        {msg && <div className={cn("rounded-lg px-3 py-2", msg.includes("Matched") ? "bg-okpale text-ok" : "bg-dangerpale text-danger")}>{msg}</div>}
      </div>
    </Dialog>
  );
}

function CopyMappingDialog({ source, allRows, onClose, onDone }: { source: TBRow | null; allRows: TBRow[]; onClose: () => void; onDone: () => void; }) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [filter, setFilter] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { if (!source) { setSelected(new Set()); setFilter(""); setMsg(""); } }, [source]);

  const candidates = useMemo(() => {
    if (!source) return [];
    const q = filter.trim().toLowerCase();
    return allRows.filter((r) => r.id !== source.id &&
      (!q || r.ledger_name.toLowerCase().includes(q) || (r.tally_group || "").toLowerCase().includes(q)));
  }, [source, allRows, filter]);

  function toggle(id: number) {
    setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  }

  async function doCopy() {
    if (!source || selected.size === 0) return;
    setBusy(true); setMsg("");
    try {
      const r = await mappingApi.copy(source.id, Array.from(selected));
      setMsg(`Copied ${source.coa_code} to ${r.copied} row(s).`);
      onDone();
      setSelected(new Set());
    } catch (e: any) { setMsg(e?.message || "Copy failed"); }
    finally { setBusy(false); }
  }

  return (
    <Dialog
      open={!!source}
      onClose={onClose}
      title="Copy mapping to other ledgers"
      size="lg"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button onClick={doCopy} disabled={selected.size === 0 || busy}>
            <CopyIcon className="h-4 w-4" />{busy ? "Copying…" : `Copy to ${selected.size} row${selected.size === 1 ? "" : "s"}`}
          </Button>
        </>
      }
    >
      {source && (
        <div className="space-y-3">
          <div className="rounded-lg bg-navy-pale px-3 py-2 text-sm">
            <span className="text-muted">Source: </span>
            <span className="font-medium text-navy">{source.ledger_name}</span>
            <span className="ml-2 font-mono text-xs text-gold">{source.coa_code}</span>
          </div>
          <Input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter target ledgers…" />
          <div className="max-h-80 overflow-y-auto rounded-lg border border-line">
            {candidates.map((r) => (
              <label key={r.id} className="flex cursor-pointer items-center gap-3 border-b border-line px-3 py-2 text-sm last:border-0 hover:bg-surface">
                <input type="checkbox" checked={selected.has(r.id)} onChange={() => toggle(r.id)} />
                <div className="flex-1">
                  <div className="text-ink">{r.ledger_name}</div>
                  <div className="text-xs text-muted">{r.tally_group || "—"}</div>
                </div>
                {r.coa_code && <span className="font-mono text-xs text-muted">currently: {r.coa_code}</span>}
              </label>
            ))}
            {candidates.length === 0 && <div className="px-3 py-6 text-center text-sm text-muted">No matching ledgers</div>}
          </div>
          {msg && <div className={cn("rounded-lg px-3 py-2 text-sm", msg.includes("Copied") ? "bg-okpale text-ok" : "bg-dangerpale text-danger")}>{msg}</div>}
        </div>
      )}
    </Dialog>
  );
}

function fmtINR(n: number | null | undefined) {
  if (n == null || n === 0) return "—";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}
