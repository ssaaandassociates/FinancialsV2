import { supabase } from "./supabase";

// Backend URL is read at BUILD time from NEXT_PUBLIC_BACKEND_URL.
// Set in Railway Variables on the frontend service.
const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "";

/**
 * Thin fetch wrapper that automatically attaches the current Supabase
 * access token as a Bearer header. Calls the backend directly when
 * BACKEND is set; falls back to /api/* path (for local dev with rewrites).
 */
async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

function url(path: string) {
  return BACKEND ? `${BACKEND}/api${path}` : `/api${path}`;
}

/**
 * Public helper to build a full backend URL for downloads (href) and direct
 * fetch() calls (file uploads) that don't go through apiGet/apiPost.
 * `path` should start with "/" and NOT include the "/api" prefix.
 */
export function backendUrl(path: string) {
  return url(path);
}

/** Bearer auth headers for direct fetch() calls (e.g. file uploads). */
export async function bearerHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers: HeadersInit = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const res = await fetch(url(path), { headers: await authHeaders() });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(url(path), {
    method: "POST",
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiPut<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(url(path), {
    method: "PUT",
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiDelete<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(url(path), {
    method: "DELETE",
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function safeText(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return res.statusText;
  }
}