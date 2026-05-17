<script lang="ts">
    import { cx, resolveDmxColorTokens, dmxBloomRootActive, dmxDotBloomParts, getPatternIndexes, remapOpacityToTriplet, objectToStyle } from '../core';
    import type { DotMatrixCommonProps } from '../core';
    import { PrefersReducedMotion, DotMatrixPhases, CyclePhase } from '../hooks.svelte';

    let {
        size = 34,
        dotSize = 5,
        color = 'currentColor',
        colorPreset,
        ariaLabel = 'Loading',
        class: className,
        muted = false,
        bloom = false,
        halo = 0,
        dotClass,
        dotShape = 'circle',
        speed = 1.45,
        animated = true,
        hoverAnimated = false,
        pattern = 'full',
        cellPadding,
        boxSize,
        minSize,
        opacityBase,
        opacityMid,
        opacityPeak
    }: DotMatrixCommonProps = $props();

    const ROW_COUNTS = [3, 4, 5, 4, 3] as const;
    const BASE_OPACITY = 0.08;
    const HIGH_OPACITY = 0.96;
    const HEX_ROW_PITCH_RATIO = Math.sqrt(3) / 2;
    const BAND_WIDTH = 0.55;

    function hexPatternIndex(row: number, rowCount: number, col: number): number {
        return row * ROW_COUNTS[2] + Math.floor((ROW_COUNTS[2] - rowCount) / 2) + col;
    }

    function clamp01(n: number | undefined) {
        if (n == null || !Number.isFinite(n)) return undefined;
        return Math.min(1, Math.max(0, n));
    }

    function pointForCell(row: number, col: number): { x: number; y: number } {
        const count = ROW_COUNTS[row] ?? 1;
        return {
            x: col - (count - 1) / 2,
            y: (row - 2) * HEX_ROW_PITCH_RATIO
        };
    }

    function triangularWave(n: number): number {
        const wrapped = ((n % 1) + 1) % 1;
        return 1 - Math.abs(wrapped * 2 - 1);
    }

    function bandGlow(distance: number): number {
        return Math.max(0, 1 - Math.abs(distance) / BAND_WIDTH);
    }

    function opacityForCell(row: number, col: number, phase: number): number {
        const { x, y } = pointForCell(row, col);
        const sweep = triangularWave(phase) * 3.9 - 1.95;
        const diagA = x * 0.86 + y * 0.5;
        const diagB = x * -0.86 + y * 0.5;
        const gateA = bandGlow(diagA - sweep);
        const gateB = bandGlow(diagB + sweep);
        const centerDistance = Math.sqrt(x * x + y * y);
        const centerFlash = Math.max(0, 1 - Math.abs(sweep) / 0.68) * Math.max(0, 1 - centerDistance / 1.9);
        const wake = 0.16 * Math.max(0, 1 - Math.abs(y - sweep * 0.22) / 1.2);

        return Math.min(HIGH_OPACITY, BASE_OPACITY + gateA * 0.7 + gateB * 0.7 + centerFlash * 0.42 + wake);
    }

    const reducedMotionState = new PrefersReducedMotion();
    let reducedMotion = $derived(reducedMotionState.value);

    const phases = new DotMatrixPhases(
        () => animated && !reducedMotion,
        () => hoverAnimated && !reducedMotion,
        () => speed
    );
    let matrixPhase = $derived(phases.phase);

    const cyclePhaseState = new CyclePhase(
        () => !reducedMotion && matrixPhase !== 'idle',
        1850,
        () => speed
    );
    let cyclePhase = $derived(cyclePhaseState.value);

    let gap = $derived(cellPadding ?? Math.max(1, Math.floor((size - dotSize * ROW_COUNTS[2]) / (ROW_COUNTS[2] - 1))));
    let colPitch = $derived(dotSize + gap);
    let rowGap = $derived(Math.max(1, colPitch * HEX_ROW_PITCH_RATIO - dotSize));
    let matrixWidth = $derived(dotSize * ROW_COUNTS[2] + gap * (ROW_COUNTS[2] - 1));
    let matrixHeight = $derived(dotSize * ROW_COUNTS.length + rowGap * (ROW_COUNTS.length - 1));
    let matrixSpan = $derived(Math.max(matrixWidth, matrixHeight));
    let outerDim = $derived(Math.max(boxSize ?? matrixSpan, minSize ?? 0));
    let useWrapper = $derived(boxSize != null || minSize != null);
    let scale = $derived(useWrapper && matrixSpan > 0 ? outerDim / matrixSpan : 1);
    
    let ob = $derived(clamp01(opacityBase));
    let om = $derived(clamp01(opacityMid));
    let op = $derived(clamp01(opacityPeak));
    let phase = $derived(reducedMotion || matrixPhase === 'idle' ? 0.12 : cyclePhase);
    let activePatternIndexes = $derived(getPatternIndexes(pattern));
    let tokens = $derived(resolveDmxColorTokens(color, colorPreset));

    let matrixStyleObj = $derived({
        width: `${matrixWidth}px`,
        height: `${matrixHeight}px`,
        '--dmx-dot-fill': tokens.dotFill,
        color: tokens.resolvedColor,
        '--dmx-dot-size': `${dotSize}px`,
        '--dmx-halo-level': halo,
        ...(ob !== undefined && { '--dmx-opacity-base': ob }),
        ...(om !== undefined && { '--dmx-opacity-mid': om }),
        ...(op !== undefined && { '--dmx-opacity-peak': op }),
        ...(useWrapper
            ? { transform: `scale(${scale})`, transformOrigin: 'center center' }
            : { minWidth: minSize ? `${minSize}px` : undefined, minHeight: minSize ? `${minSize}px` : undefined })
    });
</script>

{#snippet matrix()}
    <div
        role={useWrapper ? undefined : 'status'}
        aria-live={useWrapper ? undefined : "polite"}
        aria-label={useWrapper ? undefined : ariaLabel}
        class={cx(
            'dmx-root',
            `dmx-dot-shape-${dotShape}`,
            muted && 'dmx-muted',
            dmxBloomRootActive(bloom, halo) && 'dmx-bloom',
            !useWrapper && className
        )}
        style={objectToStyle(matrixStyleObj)}
        onmouseenter={useWrapper ? undefined : phases.onMouseEnter}
        onmouseleave={useWrapper ? undefined : phases.onMouseLeave}
    >
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: {rowGap}px; width: 100%; height: 100%;">
            {#each ROW_COUNTS as count, row}
                <div style="display: flex; justify-content: center; gap: {gap}px;">
                    {#each Array.from({ length: count }) as _, col}
                        {@const isActive = activePatternIndexes.includes(hexPatternIndex(row, count, col))}
                        {@const opacity = isActive ? opacityForCell(row, col, phase) : 0}
                        {@const dmxBloom = dmxDotBloomParts(isActive, opacity, bloom, halo, ob, om, op)}
                        <span
                            aria-hidden="true"
                            class={cx(
                                'dmx-dot',
                                !isActive && 'dmx-inactive',
                                dmxBloom.bloomDot && 'dmx-bloom-dot',
                                dotClass
                            )}
                            style={objectToStyle({
                                width: `${dotSize}px`,
                                height: `${dotSize}px`,
                                opacity: Math.round(remapOpacityToTriplet(opacity, ob, om, op) * 1e6) / 1e6,
                                '--dmx-bloom-level': dmxBloom.level
                            })}
                        ></span>
                    {/each}
                </div>
            {/each}
        </div>
    </div>
{/snippet}

{#if useWrapper}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        role="status"
        aria-live="polite"
        aria-label={ariaLabel}
        class={className}
        style={objectToStyle({
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: `${outerDim}px`,
            height: `${outerDim}px`,
            minWidth: minSize == null ? undefined : `${minSize}px`,
            minHeight: minSize == null ? undefined : `${minSize}px`,
            overflow: 'hidden'
        })}
        onmouseenter={phases.onMouseEnter}
        onmouseleave={phases.onMouseLeave}
    >
        {@render matrix()}
    </div>
{:else}
    {@render matrix()}
{/if}