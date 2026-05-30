"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";

export default function HomePage() {
  const router = useRouter();
  const { session, loading } = useAuth();

  useEffect(() => {
    if (loading) return;
    router.replace(session ? "/dashboard" : "/login");
  }, [session, loading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-sm text-muted">Loading…</div>
    </div>
  );
}
