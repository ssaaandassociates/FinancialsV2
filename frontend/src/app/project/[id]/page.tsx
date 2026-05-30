"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { TopNav } from "@/components/top-nav";
import { Card, CardBody } from "@/components/ui/card";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function ProjectPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { session, loading } = useAuth();
  useEffect(() => {
    if (!loading && !session) router.replace("/login");
  }, [session, loading, router]);
  if (loading || !session) return null;
  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Link href="/dashboard" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink">
          <ArrowLeft className="h-4 w-4" /> Back to clients
        </Link>
        <h1 className="font-display text-3xl font-semibold text-navy">Project #{params.id}</h1>
        <p className="mt-1 text-sm text-muted">Full project workspace arriving in Slices 2–4.</p>
      </main>
    </div>
  );
}
