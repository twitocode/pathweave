import type { Metadata } from "next";
import Link from "next/link";

import { Google } from "@/lib/components/svg/google";
import { getAuthLoginHref } from "@/lib/server-url";

export const metadata: Metadata = {
  title: "Sign in — PathWeave",
  description: "Sign in to PathWeave.",
};

export default function LoginPage() {
  const authLoginHref = getAuthLoginHref();

  return (
    <div className="mx-auto flex min-h-full max-w-lg flex-col justify-center px-4 py-14 sm:px-6">
      <header className="brutal-panel mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 p-4">
          <Link
            href="/"
            className="flex items-center gap-3 text-[var(--brutal-fg)] no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brutal-accent)]"
          >
            <span
              className="flex h-10 w-10 shrink-0 items-center justify-center border border-[var(--brutal-border)] bg-[var(--brutal-bg)] text-sm font-bold text-[var(--brutal-accent)]"
              aria-hidden
            >
              P
            </span>
            <span className="text-sm font-bold tracking-[0.2em] text-[var(--brutal-accent)]">
              PATHWEAVE
            </span>
          </Link>
          <span className="text-[0.65rem] font-semibold uppercase tracking-[0.12em] text-[var(--brutal-fg-muted)]">
            Auth
          </span>
        </div>
      </header>

      <main className="brutal-panel flex flex-col">
        <div className="brutal-bar">Welcome back</div>
        <div className="space-y-6 p-6 sm:p-8">
          <p className="text-center text-[var(--brutal-fg-muted)]">
            Continue with Google
          </p>

          <div className="border border-[var(--brutal-border)] bg-[var(--brutal-inset)] p-4">
            <a
              href={authLoginHref}
              className="brutal-btn-solid flex w-full items-center justify-center no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--brutal-accent)] space-x-3 "
            >
              <Google className="h-5" />
              <span>Continue with Google</span>
            </a>
          </div>

          <p className="text-center text-sm text-[var(--brutal-fg-muted)]">
            <Link href="/" className="brutal-link">
              ← Back to home
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
