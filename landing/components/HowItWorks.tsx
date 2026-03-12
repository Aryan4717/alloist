const steps = [
  { id: "agent", label: "Agent" },
  { id: "enforce", label: "enforce()" },
  { id: "check", label: "Token + Policy check" },
  { id: "result", label: "Allow / Deny / Consent" },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-4 py-16 md:py-24">
      <div className="mx-auto max-w-6xl">
        <h2 className="mb-4 text-center text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          How it works
        </h2>
        <p className="mx-auto mb-16 max-w-2xl text-center text-muted-foreground">
          Before your agent runs a sensitive action, Alloist checks token
          validity and policy rules.
        </p>
        <div className="glass-card mx-auto max-w-4xl overflow-hidden rounded-xl p-8 md:p-12">
          <div className="flex flex-col items-stretch gap-4 md:flex-row md:items-center md:justify-between md:gap-2">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-center gap-4 md:flex-1 md:flex-col md:gap-2">
                <div className="glass-card flex flex-1 items-center justify-center rounded-lg border border-primary/20 px-6 py-4 glow-primary-hover md:min-h-[60px]">
                  <span className="text-center font-medium text-foreground">
                    {step.label}
                  </span>
                </div>
                {i < steps.length - 1 && (
                  <div className="flex justify-center md:rotate-0">
                    <svg
                      className="h-6 w-6 shrink-0 rotate-90 text-muted-foreground md:rotate-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap justify-center gap-4 md:mt-12">
            <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
              Allow → Action runs
            </span>
            <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800">
              Deny → Blocked + evidence
            </span>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Consent → Human approval
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
