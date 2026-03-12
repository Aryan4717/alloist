import Link from "next/link";

export function CTA() {
  return (
    <section id="cta" className="px-4 py-16 md:py-24">
      <div className="glass-card glow-primary mx-auto max-w-3xl rounded-2xl p-12 text-center">
        <h2 className="mb-4 text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Start in 5 minutes
        </h2>
        <p className="mb-8 text-muted-foreground">
          Run Alloist locally with Docker. Mint tokens, apply policies, and gate
          your first agent action.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            href="https://github.com"
            className="rounded-lg bg-primary px-6 py-3 text-base font-medium text-primary-foreground glow-primary glow-primary-hover transition-shadow hover:bg-primary-hover"
          >
            Get Started
          </Link>
          <Link
            href="#"
            className="rounded-lg border border-border px-6 py-3 text-base font-medium text-foreground hover:bg-muted/50"
          >
            Join waitlist
          </Link>
        </div>
        <p className="mt-8 text-sm text-muted-foreground">
          Open source. ACT-lite spec. Python & Node SDKs.
        </p>
      </div>
    </section>
  );
}
