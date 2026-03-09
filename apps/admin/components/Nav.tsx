"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApiKey } from "./ApiKeyProvider";

const navItems = [
  { href: "/tokens", label: "Tokens" },
  { href: "/policies", label: "Policies" },
  { href: "/actions", label: "Live Actions" },
  { href: "/exports", label: "Evidence Exports" },
];

export function Nav() {
  const pathname = usePathname();
  const { isConfigured } = useApiKey();

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
          {!isConfigured && (
            <span className="rounded-md bg-amber-100 px-2 py-1 text-xs text-amber-800">
              API key required
            </span>
          )}
        </nav>
      </div>
    </header>
  );
}
