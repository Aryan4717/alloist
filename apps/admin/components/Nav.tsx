"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./AuthProvider";

const navItems = [
  { href: "/tokens", label: "Tokens" },
  { href: "/policies", label: "Policies" },
  { href: "/actions", label: "Live Actions" },
  { href: "/exports", label: "Evidence Exports" },
];

export function Nav() {
  const pathname = usePathname();
  const { user, orgs, orgId, setOrgId, logout, isConfigured } = useAuth();

  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link
          href="/"
          className="text-xl font-semibold tracking-tight text-foreground"
        >
          Alloist Admin
        </Link>
        <nav className="flex items-center gap-6">
          {navItems.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-medium ${
                pathname === href
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </Link>
          ))}
          {isConfigured && (
            <>
              {orgs.length > 1 && (
                <select
                  value={orgId ?? ""}
                  onChange={(e) => setOrgId(e.target.value)}
                  className="rounded-md border border-border bg-background px-2 py-1 text-sm"
                >
                  {orgs.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))}
                </select>
              )}
              <span className="text-sm text-muted-foreground">
                {user?.email}
              </span>
              <button
                onClick={logout}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
