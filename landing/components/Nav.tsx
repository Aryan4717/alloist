import Link from "next/link";

const navItems = [
  { href: "#features", label: "Product" },
  { href: "#how-it-works", label: "How it works" },
  { href: "https://github.com", label: "GitHub", external: true },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/80 bg-card/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link
          href="/"
          className="text-xl font-semibold tracking-tight text-foreground"
        >
          Alloist
        </Link>
        <nav
          className="flex items-center gap-4 md:gap-6"
          aria-label="Main navigation"
        >
          {navItems.map((item) =>
            item.external ? (
              <a
                key={item.href}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                {item.label}
              </a>
            ) : (
              <Link
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                {item.label}
              </Link>
            )
          )}
          <Link
            href="#cta"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground glow-primary glow-primary-hover transition-shadow hover:bg-primary-hover"
          >
            Get Started
          </Link>
        </nav>
      </div>
    </header>
  );
}
