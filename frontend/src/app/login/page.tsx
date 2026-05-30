"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const { session, loading } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firmName, setFirmName] = useState("");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && session) router.replace("/dashboard");
  }, [session, loading, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setMsg("");
    setBusy(true);
    try {
      if (mode === "signin") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.replace("/dashboard");
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { firm_name: firmName } },
        });
        if (error) throw error;
        setMsg("Account created. Check your email to confirm, then sign in.");
        setMode("signin");
      }
    } catch (e: any) {
      setErr(e.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between bg-navy p-12 lg:flex">
        <div className="absolute left-0 top-0 h-1.5 w-full bg-gold" />
        <div className="text-xs font-semibold tracking-[0.3em] text-white/60">
          TRUSTFACTON
        </div>
        <div>
          <h1 className="font-display text-5xl font-semibold leading-tight text-white">
            SSAA
            <br />
            Financials
          </h1>
          <p className="mt-5 max-w-sm text-lg italic text-white/70">
            Schedule III financial statements, prepared in minutes.
          </p>
          <div className="mt-6 h-1 w-16 bg-gold" />
        </div>
        <div className="text-sm text-white/50">
          Evenset Consultancy Services OPC Pvt Ltd
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full items-center justify-center px-6 lg:w-1/2">
        <div className="w-full max-w-sm rise">
          <h2 className="font-display text-3xl font-semibold text-navy">
            {mode === "signin" ? "Welcome back" : "Create your firm"}
          </h2>
          <p className="mt-2 text-sm text-muted">
            {mode === "signin"
              ? "Sign in to your firm's workspace."
              : "Set up your firm's account in seconds."}
          </p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            {mode === "signup" && (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-ink">Firm name</label>
                <Input
                  value={firmName}
                  onChange={(e) => setFirmName(e.target.value)}
                  placeholder="ABC & Associates"
                  required
                />
              </div>
            )}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@firm.com"
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
              />
            </div>

            {err && (
              <div className="rounded-lg bg-dangerpale px-3 py-2 text-sm text-danger">{err}</div>
            )}
            {msg && (
              <div className="rounded-lg bg-okpale px-3 py-2 text-sm text-ok">{msg}</div>
            )}

            <Button type="submit" size="lg" className="w-full" disabled={busy}>
              {busy ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-muted">
            {mode === "signin" ? (
              <>
                New firm?{" "}
                <button onClick={() => setMode("signup")} className="font-medium text-gold hover:underline">
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button onClick={() => setMode("signin")} className="font-medium text-gold hover:underline">
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
