import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Lazy-initialized Supabase client.
// Avoids throwing at module load time during Next.js static page generation,
// where env vars may not be available. Real users in the browser have the
// NEXT_PUBLIC_* values inlined at build time, so this works correctly at runtime.

let _client: SupabaseClient | null = null;

function getClient(): SupabaseClient {
  if (_client) return _client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  if (!url || !key) {
    // Return a stub during build-time prerender; real browser will have envs.
    if (typeof window === "undefined") {
      // Server-side / build time: return a minimal client that won't be used in practice
      return createClient("https://placeholder.supabase.co", "placeholder-key", {
        auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      });
    }
    throw new Error("Supabase env vars missing. Check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.");
  }
  _client = createClient(url, key, {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
  });
  return _client;
}

// Proxy that forwards all property access to the real client.
// Lets existing code keep using `supabase.auth.X` exactly as before.
export const supabase: SupabaseClient = new Proxy({} as SupabaseClient, {
  get(_, prop) {
    const client = getClient();
    const value = (client as any)[prop];
    return typeof value === "function" ? value.bind(client) : value;
  },
});