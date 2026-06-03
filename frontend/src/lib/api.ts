import { supabase } from "./supabase";

/**
 * Thin fetch wrapper that automatically attaches the current Supabase
 * access token as a Bearer header. All calls go to /api/* which Next.js
 * rewrites to the FastAPI backend.
 */
async function authHeaders(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`, { headers: await authHeaders() });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiPost<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiPut<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "PUT",
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new ApiError(res.status, await safeText(res));
  return res.json();
}

export async function apiDelete<T = any>(path: string, body?: any): Promise<T> {
  const res = await fetch(`/api${path}`, {
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
