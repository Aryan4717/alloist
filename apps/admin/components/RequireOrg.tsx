"use client";

import { useAuth } from "./AuthProvider";
import { usePathname } from "next/navigation";

export function RequireOrg({ children }: { children: React.ReactNode }) {
  const { orgs, isConfigured, isLoading } = useAuth();
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname.startsWith("/auth/");

  if (isAuthPage || !isConfigured || isLoading) {
    return <>{children}</>;
  }

  if (orgs.length === 0) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-8 text-center">
        <h2 className="mb-2 text-lg font-medium text-amber-900">
          No organization access
        </h2>
        <p className="text-sm text-amber-800">
          You need to be invited to an organization to use this app. Contact your
          administrator.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
