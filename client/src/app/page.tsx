import type { Metadata } from "next";
import Link from "next/link";

import { HowItWorks } from "@/lib/components/how-it-works";

export const metadata: Metadata = {
  title: "PathWeave",
  description: "Paths that connect your work — sign in when you are ready.",
};

function SiteFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="brutal-panel mt-10">
      <div className="brutal-bar">SITE</div>
      <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-[var(--brutal-fg-muted)]">
          © {year} PathWeave
        </p>
        <nav
          className="flex flex-wrap gap-x-6 gap-y-2 text-[0.65rem] font-semibold uppercase tracking-[0.12em]"
          aria-label="Footer"
        >
          <Link
            href="/"
            className="text-[var(--brutal-fg-muted)] no-underline transition-colors hover:text-[var(--brutal-accent)]"
          >
            Home
          </Link>
          <Link href="/login" className="brutal-link">
            Sign in
          </Link>
        </nav>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <div className="mx-auto flex min-h-full max-w-5xl flex-col px-4 py-6 sm:px-8 sm:py-10">
      <header className="brutal-panel mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 sm:p-5">
          <div className="flex items-center gap-3">
            <span
              className="flex h-10 w-10 shrink-0 items-center justify-center border border-[var(--brutal-border)] bg-[var(--brutal-bg)] text-sm font-bold text-[var(--brutal-accent)]"
              aria-hidden
            >
              P
            </span>
            <span className="text-sm font-bold tracking-[0.2em] text-[var(--brutal-accent)]">
              PATHWEAVE
            </span>
          </div>
          <nav className="flex flex-wrap items-center gap-2">
            <Link
              href="/login"
              className="brutal-btn-outline inline-block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brutal-accent)]"
            >
              SIGN IN
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        <section className="brutal-panel flex min-h-0 flex-col">
          <div className="brutal-bar">ABOUT</div>
          <div className="space-y-4 p-5 sm:p-6">
            <h1 className="text-base font-bold uppercase leading-snug tracking-wide text-[var(--brutal-accent)] sm:text-lg">
              Weave clarity into every path you take.
            </h1>
            <p className="text-[var(--brutal-fg-muted)]">
              Sign in through your branded entry point—then continue securely
              with AuthKit behind the scenes. Questions about access? Open the{" "}
              <Link href="/login" className="brutal-link">
                sign-in flow
              </Link>
              .
            </p>
            <div className="border-t border-[var(--brutal-border)] border-opacity-40 pt-4">
              <p className="mb-3 text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-[var(--brutal-accent)]">
                Next step
              </p>
              <Link
                href="/login"
                className="brutal-btn-solid inline-block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brutal-accent)]"
              >
                ENTER APP
              </Link>
            </div>
          </div>
        </section>

        <HowItWorks />
      </main>

      <SiteFooter />
    </div>
  );
}
