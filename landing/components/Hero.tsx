import Link from "next/link";

export function Hero() {
  return (
    <section className="relative px-4 pt-16 pb-24 md:pt-24 md:pb-32">
      <div className="mx-auto max-w-4xl text-center">
        <h1 className="mb-6 text-4xl font-bold tracking-tight text-foreground md:text-5xl lg:text-6xl">
          The AI permission layer for the Internet
        </h1>
        <p className="mb-10 text-lg text-muted-foreground md:text-xl">
          Control what AI agents can do via capability tokens and policy
          enforcement. Gate email, payments, and sensitive actions before they
          run.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            href="#cta"
            className="rounded-lg bg-primary px-6 py-3 text-base font-medium text-primary-foreground glow-primary glow-primary-hover transition-shadow hover:bg-primary-hover"
          >
            Get Started
          </Link>
          <Link
            href="#code-example"
            className="rounded-lg border border-border bg-card/60 px-6 py-3 text-base font-medium text-foreground backdrop-blur-sm hover:bg-muted/50"
          >
            See Demo
          </Link>
        </div>
        <div className="mt-16 rounded-xl border border-border/80 bg-card/60 p-6 text-left backdrop-blur-sm">
          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            One line of code
          </p>
          <pre className="overflow-x-auto text-sm text-foreground">
            <code>
              {`enforce(action="gmail.send", metadata={"to": to})  # Blocks if policy denies`}
            </code>
          </pre>
        </div>
      </div>
    </section>
  );
}
