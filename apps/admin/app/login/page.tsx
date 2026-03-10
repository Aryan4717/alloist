"use client";

import { useAuth } from "@/components/AuthProvider";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const { loginWithGoogle, loginWithGitHub, isConfigured, isLoading } =
    useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isConfigured) {
      router.replace("/");
    }
  }, [isLoading, isConfigured, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-xl border border-border bg-card p-8 shadow-sm">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-foreground">
          Sign in to Alloist Admin
        </h1>
        <p className="mb-6 text-muted-foreground">
          Use your Google or GitHub account to continue.
        </p>
        <div className="flex flex-col gap-3">
          <button
            onClick={loginWithGoogle}
            className="rounded-lg border border-border bg-background px-4 py-3 font-medium text-foreground hover:bg-muted"
          >
            Login with Google
          </button>
          <button
            onClick={loginWithGitHub}
            className="rounded-lg border border-border bg-background px-4 py-3 font-medium text-foreground hover:bg-muted"
          >
            Login with GitHub
          </button>
        </div>
      </div>
    </div>
  );
}
