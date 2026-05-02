const STEPS = [
  {
    title: "Connect & set your goals",
    detail:
      "Tell PathWeave what you are working on—tasks, files, or projects—and define what done looks like in seconds.",
  },
  {
    title: "Sign in & stay secure",
    detail:
      "Authorize through AuthKit-backed sign-in. Tokens and session hand-offs stay behind the scenes while you move forward.",
  },
  {
    title: "Review, control & improve",
    detail:
      "Stay in control from one place: revisit results, adjust how PathWeave supports you, and refine your workflow over time.",
  },
] as const;

export function HowItWorks() {
  return (
    <section className="brutal-panel mt-8" aria-labelledby="how-it-works-title">
      <div className="p-6 sm:p-8 lg:p-10">
        <h2
          id="how-it-works-title"
          className="max-w-xl text-[clamp(1.75rem,3vw,2.75rem)] font-semibold leading-[1.15] tracking-tight text-[var(--brutal-fg)]"
          style={{ fontFamily: "var(--font-sans-display)" }}
        >
          Get started
          <br />
          in minutes.
        </h2>
        <p
          className="mt-4 max-w-md text-sm leading-relaxed text-[var(--brutal-fg-muted)] sm:mt-3"
          style={{ fontFamily: "var(--font-mono-display)" }}
        >
          Three simple steps, then you&apos;re in.
        </p>

        {/* Title | step # | detail — badges sit in the center column */}
        <div className="mt-8 grid grid-cols-1 gap-y-4 sm:mt-10 sm:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] sm:items-center sm:gap-x-10 sm:gap-y-8">
          {STEPS.map((step, i) => (
            <div key={step.title} className="contents">
              <h3
                className="min-w-0 text-[1.1rem] font-semibold leading-snug tracking-tight text-[var(--brutal-fg)] sm:text-[1.15rem]"
                style={{ fontFamily: "var(--font-sans-display)" }}
              >
                {step.title}
              </h3>
              <span className="mx-auto grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[var(--brutal-accent)] text-[0.7rem] font-semibold text-white tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p
                className="min-w-0 text-sm leading-relaxed text-[var(--brutal-fg-muted)]"
                style={{ fontFamily: "var(--font-mono-display)" }}
              >
                {step.detail}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
