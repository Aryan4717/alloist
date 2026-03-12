import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { HowItWorks } from "@/components/HowItWorks";
import { CodeExample } from "@/components/CodeExample";
import { CTA } from "@/components/CTA";

export default function HomePage() {
  return (
    <>
      <Nav />
      <main id="main">
        <Hero />
        <Features />
        <HowItWorks />
        <CodeExample />
        <CTA />
      </main>
      <footer className="border-t border-border bg-card/60 px-4 py-8 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl text-center text-sm text-muted-foreground">
          Alloist – The AI permission layer for the Internet
        </div>
      </footer>
    </>
  );
}
