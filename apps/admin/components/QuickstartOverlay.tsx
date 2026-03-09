"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";

const STORAGE_KEY = "alloist_quickstart_dismissed";

export function QuickstartOverlay() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem(STORAGE_KEY);
    if (!dismissed) setOpen(true);
  }, []);

  const dismiss = useCallback(() => {
    setOpen(false);
    localStorage.setItem(STORAGE_KEY, "1");
  }, []);

  if (!open) return null;

  const steps = [
    {
      title: "1. Start services",
      cmd: "cd backend/token_service && docker compose up -d",
    },
    {
      title: "2. Create token",
      desc: "Use the Tokens page or:",
      cmd: 'curl -X POST http://localhost:8000/tokens -H "X-API-Key: dev-api-key" -H "Content-Type: application/json" -d \'{"subject":"demo","scopes":["email:send"],"ttl_seconds":3600}\'',
    },
    {
      title: "3. Add policy",
      desc: "Use a template on the Policies page (e.g. gmail_external_send_deny)",
    },
    {
      title: "4. Run agent",
      cmd: "python backend/demos/gmail_block_demo/agent.py <token_from_step_2>",
    },
    {
      title: "5. See block",
      desc: "View the evidence in Live Actions.",
    },
  ];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-border bg-card p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-foreground">
            Protect a demo agent in 5 minutes
          </h2>
          <button
            onClick={dismiss}
            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <p className="mb-6 text-sm text-muted-foreground">
          Quick start guide to protect an AI agent with Alloist.
        </p>
        <ol className="space-y-6">
          {steps.map((s, i) => (
            <li key={i}>
              <h3 className="font-medium text-foreground">{s.title}</h3>
              {s.desc && (
                <p className="mt-1 text-sm text-muted-foreground">{s.desc}</p>
              )}
              {s.cmd && (
                <div className="mt-2 flex items-center gap-2">
                  <code className="flex-1 rounded-md border border-border bg-muted/50 px-3 py-2 font-mono text-xs text-foreground break-all">
                    {s.cmd}
                  </code>
                  <button
                    onClick={() => copyToClipboard(s.cmd)}
                    className="shrink-0 rounded-md border border-border px-2 py-1.5 text-xs font-medium hover:bg-muted"
                  >
                    Copy
                  </button>
                </div>
              )}
            </li>
          ))}
        </ol>
        <div className="mt-2 flex items-center gap-4">
          <Link
            href="/tokens"
            onClick={dismiss}
            className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover"
          >
            Go to Tokens
          </Link>
          <Link
            href="/actions"
            onClick={dismiss}
            className="text-sm font-medium text-primary hover:underline"
          >
            Live Actions →
          </Link>
        </div>
      </div>
    </div>
  );
}
