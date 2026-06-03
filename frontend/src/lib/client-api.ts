import { apiGet, apiPost, apiPut, apiDelete, backendUrl, bearerHeaders } from "@/lib/api";

// ---------- Types (matching backend models) ----------

export interface ClientFull {
  id: number;
  name: string;
  cin?: string | null;
  pan?: string | null;
  gstin?: string | null;
  date_of_incorporation?: string | null;
  registered_office?: string | null;
  principal_activity?: string | null;
  auditor_name?: string | null;
  auditor_frn?: string | null;
  auditor_membership_no?: string | null;
  face_value?: number;
  authorised_shares?: number;
  authorised_capital?: number;
  subscribed_shares?: number;
  subscribed_capital?: number;
  paidup_shares?: number;
  paidup_capital?: number;
  projects?: { id: number; fy: string; status: string }[];
}

export interface Director {
  id: number;
  client_id: number;
  name: string;
  din?: string;
  designation?: string;
  date_of_appointment?: string | null;
  pan?: string;
  is_kmp: boolean;
  signs_financials: boolean;
  is_active: boolean;
}

export interface Shareholder {
  id: number;
  client_id: number;
  name: string;
  no_of_shares_cy?: number;
  no_of_shares_py?: number;
  face_value?: number;
  pct_holding_cy?: number;
  pct_holding_py?: number;
  is_promoter: boolean;
  is_director: boolean;
  din?: string;
  pan?: string;
}

export interface Policy {
  id: number;
  client_id: number;
  policy_number: number;
  title: string;
  body: string;
  is_active: boolean;
}

export interface CustomCoA {
  id: number;
  client_id: number;
  code: string;
  particulars: string;
  parent_code?: string;
  nature?: string;
  fs_type?: string;
  note_ref?: string;
}

export interface ProjectRow {
  id: number;
  client_id: number;
  financial_year: string;
  status: string;
  bs_date_cy?: string;
  bs_date_py?: string;
  company_type?: string;
}

// ---------- API ----------

export const clientApi = {
  get:    (id: number)                 => apiGet<ClientFull>(`/clients/${id}`),
  update: (id: number, p: Partial<ClientFull>) => apiPut(`/clients/${id}`, p),
  remove: (id: number, confirmName: string)    => apiDelete(`/clients/${id}`, { confirm_name: confirmName }),
};

export const directorsApi = {
  list:   (clientId: number)         => apiGet<Director[]>(`/directors/${clientId}`),
  create: (d: Partial<Director>)     => apiPost<Director>("/directors/", d),
  update: (id: number, d: Partial<Director>) => apiPut(`/directors/${id}`, d),
  remove: (id: number)               => apiDelete(`/directors/${id}`),
};

export const shareholdersApi = {
  list:   (clientId: number)            => apiGet<Shareholder[]>(`/client-shareholders/${clientId}`),
  create: (s: Partial<Shareholder>)     => apiPost<Shareholder>("/client-shareholders/", s),
  update: (id: number, s: Partial<Shareholder>) => apiPut(`/client-shareholders/${id}`, s),
  remove: (id: number)                  => apiDelete(`/client-shareholders/${id}`),
};

export const policiesApi = {
  list:   (clientId: number)         => apiGet<Policy[]>(`/client-policies/${clientId}`),
  create: (p: Partial<Policy>)       => apiPost<Policy>("/client-policies/", p),
  update: (id: number, p: Partial<Policy>) => apiPut(`/client-policies/${id}`, p),
  remove: (id: number)               => apiDelete(`/client-policies/${id}`),
};

export const customCoAApi = {
  list:   (clientId: number)         => apiGet<CustomCoA[]>(`/custom-coa/${clientId}`),
  create: (c: Partial<CustomCoA>)    => apiPost<CustomCoA>("/custom-coa/", c),
  update: (id: number, c: Partial<CustomCoA>) => apiPut(`/custom-coa/${id}`, c),
  remove: (id: number)               => apiDelete(`/custom-coa/${id}`),
};

export const projectsApi = {
  list:      (clientId?: number)            => apiGet<ProjectRow[]>(`/projects/${clientId !== undefined ? "?client_id=" + clientId : ""}`),
  create:    (p: Partial<ProjectRow>)       => apiPost<ProjectRow>("/projects/", p),
  duplicate: (id: number)                   => apiPost(`/projects/${id}/duplicate`),
  remove:    (id: number)                   => apiDelete(`/projects/${id}`),
};

// Paths (NOT full URLs) — passed to downloadFile() which adds the backend
// host + auth header. Plain <a href> can't send the Bearer token.
export const templatePaths = {
  blank:    "/templates/master-blank",
  current:  (clientId: number) => `/templates/master-current/${clientId}`,
  ppe:      "/templates/ppe",
};

// ---------- Master data import ----------
export interface MasterImportResult {
  sheets_processed: string[];
  warnings: string[];
  client_master_fields_updated?: number;
  directors?: { created: number; updated: number };
  shareholders?: { created: number; updated: number };
  custom_coa?: { created: number; updated: number };
  policies?: { created: number; updated: number };
}

export async function importMasterData(clientId: number, file: File): Promise<MasterImportResult> {
  const fd = new FormData();
  fd.append("file", file);
  const headers = await bearerHeaders();
  const res = await fetch(backendUrl(`/templates/master-import/${clientId}`), {
    method: "POST", body: fd, headers,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ---------- Sample data loader ----------
export async function loadSampleData(): Promise<{ status: string; companies: { id: number; name: string }[] }> {
  return apiPost("/sample-data/load", {});
}
