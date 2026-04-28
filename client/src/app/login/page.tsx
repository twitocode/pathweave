import type { Metadata } from "next";
import Link from "next/link";

import { getAuthLoginHref } from "@/lib/server-url";

export const metadata: Metadata = {
  title: "Sign in — PathWeave",
  description: "Sign in to PathWeave.",
};

export default function LoginPage() {
  const authLoginHref = getAuthLoginHref();

  return (
    <div className="relative min-h-full overflow-hidden bg-[#faf9f7] dark:bg-[#07080c]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_85%_60%_at_50%_-10%,rgba(13,148,136,0.18),transparent_55%),linear-gradient(to_bottom,rgba(15,23,42,0.05),transparent_35%)] dark:bg-[radial-gradient(ellipse_85%_60%_at_50%_-10%,rgba(45,212,191,0.12),transparent_55%)]"
      />
      <div className="relative mx-auto flex min-h-full max-w-xl flex-col justify-center px-6 pb-24 pt-20 sm:px-8 md:pb-32">
        <header className="mb-14 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-3 text-[#0f172a] no-underline dark:text-[#f1f5f9]"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0d9488] text-lg font-semibold text-white shadow-sm shadow-teal-900/25 dark:bg-teal-500 dark:shadow-teal-900/40">
              P
            </span>
            <span className="text-lg font-semibold tracking-tight">
              PathWeave
            </span>
          </Link>
        </header>

        <main>
          <div className="rounded-3xl border border-black/[0.06] bg-white/80 p-10 shadow-xl shadow-teal-900/[0.04] backdrop-blur-md dark:border-white/[0.08] dark:bg-[#111318]/90 dark:shadow-black/40 sm:p-12">
            <h1 className="text-center text-3xl font-semibold tracking-tight text-[#0f172a] dark:text-[#f8fafc] sm:text-[1.75rem] sm:leading-tight">
              Welcome back
            </h1>
            <p className="mx-auto mt-3 max-w-sm text-center text-base leading-relaxed text-[#475569] dark:text-[#94a3b8]">
              Continue to PathWeave. You will be redirected to FastAPI auth
              routes and then returned here after sign-in.
            </p>

            <div className="mt-10 flex flex-col gap-4">
              <a
                href={authLoginHref}
                className="flex w-full items-center justify-center rounded-xl bg-[#0d9488] px-6 py-[0.875rem] text-base font-semibold text-white shadow-md shadow-teal-900/20 transition hover:bg-[#0f766e] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0d9488] dark:bg-teal-500 dark:hover:bg-teal-400 dark:focus-visible:outline-teal-400"
              >
                Continue with Google
              </a>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
