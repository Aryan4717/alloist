import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      <div className="rounded-xl border border-border bg-card p-8 shadow-sm">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight text-foreground">
          Welcome to Alloist Admin
        </h1>
        <p className="mb-6 text-muted-foreground">
          Manage tokens, policies, and view enforcement evidence.
        </p>
        <div className="flex gap-4">
          <Link
            href="/tokens"
            className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover"
          >
            Tokens
          </Link>
          <Link
            href="/policies"
            className="rounded-lg border border-border px-4 py-2 font-medium text-foreground hover:bg-muted"
          >
            Policies
          </Link>
          <Link
            href="/actions"
            className="rounded-lg border border-border px-4 py-2 font-medium text-foreground hover:bg-muted"
          >
            Live Actions
          </Link>
        </div>
      </div>
    </div>
  );
}
