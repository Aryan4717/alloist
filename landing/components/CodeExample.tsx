export function CodeExample() {
  const code = `from alloist import init, enforce

init(api_key=os.environ["ALLOIST_TOKEN"])

# Gate before any sensitive action
enforce(action="gmail.send", metadata={"to": to})
send_email(to, body)  # Only runs if allowed`;

  return (
    <section id="code-example" className="px-4 py-16 md:py-24">
      <div className="mx-auto max-w-4xl">
        <h2 className="mb-4 text-center text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          One line of code
        </h2>
        <p className="mx-auto mb-12 max-w-2xl text-center text-muted-foreground">
          Add enforce() before any action. If policy denies, Alloist blocks and
          raises—your action never runs.
        </p>
        <div className="glass-card overflow-hidden rounded-xl">
          <div className="border-b border-border bg-muted/30 px-4 py-2">
            <span className="text-xs font-medium text-muted-foreground">
              Python
            </span>
          </div>
          <pre className="overflow-x-auto p-6 text-sm text-foreground">
            <code>{code}</code>
          </pre>
        </div>
      </div>
    </section>
  );
}
