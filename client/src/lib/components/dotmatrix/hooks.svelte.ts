import type { DotMatrixPhase } from './core';

export class PrefersReducedMotion {
    value = $state(false);
    constructor() {
        $effect(() => {
            const query = window.matchMedia('(prefers-reduced-motion: reduce)');
            const update = () => this.value = query.matches;
            update();
            query.addEventListener('change', update);
            return () => query.removeEventListener('change', update);
        });
    }
}

export class CyclePhase {
    value = $state(0);
    constructor(active: () => boolean, cycleMsBase: number, speed: () => number = () => 1) {
        $effect(() => {
            if (!active()) {
                this.value = 0;
                return;
            }
            const s = speed();
            const safeSpeed = s > 0 ? s : 1;
            const cycleMs = cycleMsBase / safeSpeed;
            const start = performance.now();
            let rafId: number;
            const tick = (now: number) => {
                const elapsed = Math.max(0, now - start);
                this.value = (elapsed % cycleMs) / cycleMs;
                rafId = requestAnimationFrame(tick);
            };
            rafId = requestAnimationFrame(tick);
            return () => cancelAnimationFrame(rafId);
        });
    }
}

export class SteppedCycle {
    value = $state(0);
    constructor(active: () => boolean, cycleMsBase: number, steps: number, speed: () => number = () => 1, idleStep = 0) {
        this.value = active() ? 0 : idleStep;
        
        $effect(() => {
            if (!active()) {
                this.value = idleStep;
                return;
            }
            const s = speed();
            const safeSpeed = s > 0 ? s : 1;
            const rawCycleMs = cycleMsBase / safeSpeed;
            const safeSteps = Math.max(1, Math.floor(steps));
            const stepMs = rawCycleMs / safeSteps;
            const cycleMs = stepMs * safeSteps;

            const start = performance.now();
            let currentStep = idleStep;
            let rafId: number;

            const tick = (now: number) => {
                const elapsed = Math.max(0, now - start);
                const nextStep = Math.floor((elapsed % cycleMs) / stepMs) % safeSteps;
                if (nextStep !== currentStep) {
                    currentStep = nextStep;
                    this.value = nextStep;
                }
                rafId = requestAnimationFrame(tick);
            };
            rafId = requestAnimationFrame(tick);
            return () => cancelAnimationFrame(rafId);
        });
    }
}

export class DotMatrixPhases {
    phase: DotMatrixPhase = $derived.by(() => {
        const autoRun = this.animated() && !this.hoverAnimated();
        return autoRun ? 'loadingRipple' : this.hoverAnimated() ? this.internalHoverPhase : 'idle';
    });
    
    internalHoverPhase: DotMatrixPhase = $state('idle');
    
    animated: () => boolean;
    hoverAnimated: () => boolean;
    speed: () => number;
    hoverGen = 0;
    timeoutId: number | undefined;

    constructor(animated: () => boolean, hoverAnimated: () => boolean, speed: () => number = () => 1) {
        this.animated = animated;
        this.hoverAnimated = hoverAnimated;
        this.speed = speed;
        
        $effect(() => {
            const _ = this.animated();
            const __ = this.hoverAnimated();
            this.hoverGen++;
            clearTimeout(this.timeoutId);
        });
    }

    onMouseEnter = () => {
        const autoRun = this.animated() && !this.hoverAnimated();
        if (!this.hoverAnimated() || autoRun) return;
        clearTimeout(this.timeoutId);
        const gen = ++this.hoverGen;
        this.internalHoverPhase = 'collapse';
        const s = this.speed();
        const collapseMs = Math.max(1, Math.round(300 / (s > 0 ? s : 1)));
        this.timeoutId = window.setTimeout(() => {
            if (this.hoverGen !== gen) return;
            this.internalHoverPhase = 'hoverRipple';
        }, collapseMs);
    };

    onMouseLeave = () => {
        const autoRun = this.animated() && !this.hoverAnimated();
        if (!this.hoverAnimated() || autoRun) return;
        this.hoverGen++;
        clearTimeout(this.timeoutId);
        this.internalHoverPhase = 'idle';
    };
}