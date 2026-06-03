import { apiGet, apiPost, apiPut, apiDelete, backendUrl, bearerHeaders } from "@/lib/api";

// ============ Audit ============
export interface AuditEntry {
  id: number; project_id: number; entry_number?: string;
  date?: string; description: string;
  dr_coa_code: string; cr_coa_code: string; amount: number;
  status: "proposed" | "approved" | "posted";
}
export const auditApi = {
  list:   (pid: number) => apiGet<AuditEntry[]>(`/audit/${pid}`),
  create: (e: Partial<AuditEntry>) => apiPost<AuditEntry>("/audit/", e),
  update: (id: number, e: Partial<AuditEntry>) => apiPut(`/audit/${id}`, e),
  remove: (id: number) => apiDelete(`/audit/${id}`),
  check:  (pid: number) => apiGet<{ total: number; balanced: boolean; dr_total: number; cr_total: number }>(`/audit/${pid}/check`),
};

// ============ Ageing (TR / TP derived) ============
export interface AgeingMatrix {
  cy: { rows: Record<string, Record<string, number>>; grand_total: number };
  py: { rows: Record<string, Record<string, number>>; grand_total: number };
  buckets: string[];
  categories: string[];
}
export const ageingApi = {
  tr: (pid: number) => apiGet<AgeingMatrix>(`/ageing/${pid}/schedule/tr`),
  tp: (pid: number) => apiGet<AgeingMatrix>(`/ageing/${pid}/schedule/tp`),
};

// ============ Ratios PY-1 + computed ============
export interface RatioPY1Row {
  ratio_key: string; py1_numerator?: number; py1_denominator?: number;
}
export interface ComputedRatio {
  key: string; name: string; numerator_desc: string; denominator_desc: string;
  cy_value?: number; py_value?: number; variance_pct?: number; flagged: boolean;
}
export const ratiosApi = {
  py1Get:  (pid: number) => apiGet<RatioPY1Row[]>(`/ratio-py1/${pid}`),
  py1Save: (data: { project_id: number; ratios: RatioPY1Row[] }) => apiPost("/ratio-py1/", data),
  compute: (pid: number) => apiPost<{ ratios: ComputedRatio[]; eps: any }>(`/generate/${pid}/ratios`),
};

// ============ Related Parties ============
export interface RelatedParty {
  id: number; project_id: number; name: string;
  category: "KMP" | "Director" | "Holding" | "Subsidiary" | "Associate" | "Joint Venture" | "Enterprise where KMP has significant influence" | "Other";
  relationship?: string;
}
export interface RPTransaction {
  id: number; project_id: number; party_id: number;
  transaction_type: string; cy_amount?: number; py_amount?: number; cy?: number; py?: number;
}
export interface KMPCandidate { name: string; din?: string; designation?: string; pan?: string; category_suggestion: string; }

export const rpApi = {
  listParties: (pid: number) => apiGet<RelatedParty[]>(`/related-parties/${pid}`),
  createParty: (p: Partial<RelatedParty>) => apiPost<RelatedParty>("/related-parties/", p),
  removeParty: (id: number) => apiDelete(`/related-parties/${id}`),
  txnsForParty: (party_id: number) => apiGet<RPTransaction[]>(`/rp-transactions/party/${party_id}`),
  createTxn:   (t: Partial<RPTransaction>) => apiPost<RPTransaction>("/rp-transactions/", t),
  updateTxn:   (id: number, t: Partial<RPTransaction>) => apiPut(`/rp-transactions/${id}`, t),
  removeTxn:   (id: number) => apiDelete(`/rp-transactions/${id}`),
  kmpCandidates: (pid: number) => apiGet<KMPCandidate[]>(`/rp/kmp-candidates/${pid}`),
  autoKMP:     (pid: number) => apiPost<{ added: number }>(`/rp/auto-kmp/${pid}`),
};

// ============ Closing Stock + PPE ============
export interface ClosingStockRow {
  id?: number; project_id: number;
  stock_type: string;
  cy_amount?: number; py_amount?: number;
}
export const stockApi = {
  list: (pid: number) => apiGet<ClosingStockRow[]>(`/closing-stock/${pid}`),
  save: (r: ClosingStockRow) => apiPost("/closing-stock/", r),
  types: (pid: number) => apiGet<string[]>(`/closing-stock/${pid}/types`),
};

export interface PPEEntry {
  id: number; project_id: number; coa_code: string; particulars: string;
  gross_opening_cy?: number; gross_additions_cy?: number; gross_disposals_cy?: number;
  dep_opening_cy?: number; dep_for_year_cy?: number; dep_on_disposals_cy?: number;
  gross_opening_py?: number; gross_additions_py?: number; gross_disposals_py?: number;
  dep_opening_py?: number; dep_for_year_py?: number; dep_on_disposals_py?: number;
}
export const ppeApi = {
  list: (pid: number) => apiGet<PPEEntry[]>(`/ppe/${pid}`),
  update: (id: number, e: Partial<PPEEntry>) => apiPut(`/ppe/${id}`, e),
};

// ============ Signing + Profile + Disclosures ============
export interface SigningBlock {
  id?: number; project_id: number;
  auditor_firm?: string; auditor_frn?: string; auditor_partner?: string;
  auditor_membership_no?: string; udin?: string; place?: string; date?: string;
  director1_name?: string; director1_din?: string; director1_designation?: string;
  director2_name?: string; director2_din?: string; director2_designation?: string;
}
export const signingApi = {
  get:          (pid: number) => apiGet<SigningBlock>(`/signing/${pid}`),
  save:         (b: SigningBlock) => apiPost("/signing/", b),
  autoPopulate: (pid: number) => apiPost(`/signing/${pid}/auto-populate`),
};

export interface CompanyProfile {
  id?: number; project_id: number;
  company_type?: string;
  cif_imports?: number; cif_components?: number; cif_capital_goods?: number;
  fob_exports?: number; forex_earnings?: number; forex_expenditure?: number;
}
export const profileApi = {
  get:  (pid: number) => apiGet<CompanyProfile>(`/profile/${pid}`),
  save: (p: CompanyProfile) => apiPost("/profile/", p),
};

export interface DisclosureSection {
  id: number; project_id: number; section_ref: string; title: string;
  items: { id: number; particulars: string; cy?: number; py?: number; notes?: string }[];
}
export const disclosuresApi = {
  list: (pid: number) => apiGet<Record<string, DisclosureSection>>(`/disclosures/${pid}`),
  updateItem: (item_id: number, data: { cy?: number; py?: number; notes?: string }) =>
    apiPut(`/disclosures/${item_id}`, data),
};

// ============ Generate / Preview ============
export interface BSLine {
  particulars: string; note_ref?: string; cy?: number; py?: number;
  level: number; is_total?: boolean; is_section?: boolean;
}
export interface PLLine extends BSLine {}
export interface NoteSection {
  ref: string; title: string;
  lines: { particulars: string; cy?: number; py?: number; is_total?: boolean }[];
}
export interface CashFlowSection {
  title: string;
  lines: { particulars: string; cy?: number; py?: number; is_total?: boolean }[];
}

export const generateApi = {
  bs:       (pid: number) => apiGet<BSLine[]>(`/generate/${pid}/bs`),
  pl:       (pid: number) => apiGet<PLLine[]>(`/generate/${pid}/pl`),
  notes:    (pid: number) => apiGet<NoteSection[]>(`/generate/${pid}/notes`),
  cashflow: (pid: number) => apiGet<CashFlowSection[]>(`/generate/${pid}/cashflow`),
  eps:      (pid: number) => apiPost(`/generate/${pid}/eps`),
  ratios:   (pid: number) => apiPost<{ ratios: ComputedRatio[]; eps?: any }>(`/generate/${pid}/ratios`),
  all:      (pid: number) => apiGet(`/generate/${pid}/all`),
  validate: (pid: number) => apiGet<any>(`/validate/${pid}`),
  lineDetail: (pid: number, note_ref: string) =>
    apiGet<{ note_ref: string; ledgers: { ledger_name: string; coa_code: string; cy_net: number; py_net: number; tb_row_id: number }[]; cy_total: number; py_total: number }>(`/preview/${pid}/line-detail?note_ref=${encodeURIComponent(note_ref)}`),
};

export const exportRoutes = {
  excel: (pid: number) => backendUrl(`/export/${pid}/excel`),
  pdf:   (pid: number) => backendUrl(`/export/${pid}/pdf`),
  generate: (pid: number) => backendUrl(`/export/${pid}/generate`),
};

// ---------- PPE template + import ----------
export const ppeTemplate = {
  downloadUrl: backendUrl("/templates/ppe"),
  import: async (projectId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const headers = await bearerHeaders();
    const res = await fetch(backendUrl(`/templates/ppe-import/${projectId}`), {
      method: "POST", body: fd, headers,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<{ created: number; updated: number }>;
  },
};
