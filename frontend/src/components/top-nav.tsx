"use client";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export function TopNav() {
  const { session, signOut } = useAuth();
  const email = session?.user?.email;
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-white/85 backdrop-blur">
      <div className="absolute left-0 top-0 h-[3px] w-full bg-gold" />
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="font-display text-xl font-semibold text-navy">
            SSAA <span className="text-gold">Financials</span>
          </div>
          <div className="hidden text-[10px] font-semibold tracking-[0.25em] text-muted sm:block">
            TRUSTFACTON
          </div>
        </Link>
        <div className="flex items-center gap-3">
          {email && <span className="hidden text-sm text-muted sm:block">{email}</span>}
          <Button variant="ghost" size="sm" onClick={() => signOut()}>
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </div>
      </div>
    </header>
  );
}
