import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "PathWeave",
  description: "Paths that connect your work — sign in when you are ready.",
};

export default function Home() {
  return (
    <div className="relative min-h-full flex flex-col bg-[#faf9f7] dark:bg-[#07080c]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_55%_at_50%_-20%,rgba(13,148,136,0.12),transparent)] dark:bg-[radial-gradient(ellipse_80%_55%_at_50%_-20%,rgba(45,212,191,0.08),transparent)]"
      />
      <header className="relative z-10 flex items-center justify-between border-b border-black/[0.05] px-6 py-5 dark:border-white/[0.06] sm:px-10">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0d9488] text-sm font-semibold text-white dark:bg-teal-500">
            P
          </span>
          <span className="text-[0.9375rem] font-semibold tracking-tight text-[#0f172a] dark:text-[#f1f5f9]">
            PathWeave
          </span>
        </div>
        <nav>
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 text-sm font-medium text-[#0d9488] transition hover:bg-[#0d9488]/10 dark:text-teal-400 dark:hover:bg-teal-500/10"
          >
            Sign in
          </Link>
        </nav>
      </header>

      <main className="relative z-10 flex flex-1 flex-col justify-center px-6 pb-20 pt-16 sm:px-10 md:mx-auto md:max-w-2xl md:text-center lg:pb-28">
        <h1 className="text-[2rem] font-semibold leading-[1.15] tracking-tight text-[#0f172a] dark:text-[#f8fafc] sm:text-5xl md:text-[2.75rem]">
          Weave clarity into every path you take.
        </h1>
        <p className="mx-auto mt-5 max-w-lg text-[1rem] leading-relaxed text-[#475569] dark:text-[#94a3b8] md:text-lg">
          Sign in through your branded entry point—then continue securely with
          AuthKit behind the scenes.
        </p>
        <div className="mt-12 flex flex-col gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-xl bg-[#0d9488] px-8 py-3.5 text-base font-semibold text-white shadow-md shadow-teal-900/15 transition hover:bg-[#0f766e] dark:bg-teal-500 dark:hover:bg-teal-400"
          >
            Sign in
          </Link>
        </div>
      </main>
    </div>
  );
}
