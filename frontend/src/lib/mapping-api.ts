import { apiGet, apiPost, backendUrl, bearerHeaders } from "@/lib/api";

export interface TBRow {
  id: number;
  project_id: number;
  ledger_name: string;
  tally_group: string | null;
  coa_code: string | null;
  cy_debit: number;
  cy_credit: number;
  cy_net: number;
  py_debit: number;
  py_credit: number;
  py_net: number;
}

export interface CoACode {
  code: string;
  level: number;
  particulars: string;
  schedule_ref: string | null;
  nature: string | null;
  fs_type: string | null;
  note_ref: string | null;
  tally_group: string | null;
}

export interface MappingSummary {
  total: number;
  mapped: number;
  unmapped: number;
  custom_coa: number;
}

export interface AutoMapResult {
  total_rows: number;
  mapped_by_keyword: number;
  mapped_by_tally_group: number;
  unmapped: number;
  low_confidence: number;
}

export interface PrevProjectOpt {
  id: number;
  financial_year: string;
  status: string;
  mapping_count: number;
}

export const tbApi = {
  list:           (projectId: number)         => apiGet<TBRow[]>(`/tb/${projectId}`),
  upload:         async (projectId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    // Don't use apiPost (it JSON-encodes); send FormData with auth header only
    const headers = await bearerHeaders();
    const res = await fetch(backendUrl(`/upload-tb/${projectId}`), { method: "POST", body: fd, headers });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  importMappedTB: async (projectId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const headers = await bearerHeaders();
    const res = await fetch(backendUrl(`/import-mapped-tb/${projectId}`), { method: "POST", body: fd, headers });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

export const mappingApi = {
  autoMap:    (projectId: number, force = false) =>
    apiPost<AutoMapResult>(`/map/${projectId}/auto?force=${force}`),
  setManual:  (tb_row_id: number, coa_code: string) =>
    apiPost("/map/manual", { tb_row_id, coa_code }),
  saveBatch:  (mappings: { tb_row_id: number; coa_code: string }[]) =>
    apiPost<{ saved: number; total: number }>("/map/batch", { mappings }),
  copy:       (source_tb_row_id: number, target_tb_row_ids: number[]) =>
    apiPost<{ copied: number; coa_code: string }>("/map/copy",
      { source_tb_row_id, target_tb_row_ids }),
  summary:    (projectId: number) =>
    apiGet<MappingSummary>(`/map/${projectId}/summary`),
  listCoA:    (fsType?: "BS" | "PL") =>
    apiGet<CoACode[]>(`/coa/${fsType ? `?fs_type=${fsType}` : ""}`),
  importPrev: (source_project_id: number, target_project_id: number) =>
    apiPost<{ matched: number; skipped: number; source_fy: string; source_total_mappings: number }>(
      "/map/import-previous", { source_project_id, target_project_id }),
  listPrevProjects: (projectId: number) =>
    apiGet<PrevProjectOpt[]>(`/map/previous-projects/${projectId}`),
};

export const exportPaths = {
  mappedTB:  (projectId: number) => `/export-mapped-tb/${projectId}`,
  tbTemplate: "/tb-template/tally",
  tbTemplateGeneric: "/tb-template/generic",
};
