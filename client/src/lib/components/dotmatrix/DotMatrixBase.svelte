<script lang="ts">
    import { cx, getPatternIndexes, indexToCoord, distanceFromCenter, polarAngle, normalizedRadius, manhattanDistance, getMatrix5Layout, resolveDmxBoxOuterDim, clamp01Dmx, resolveDmxColorTokens, remapOpacityToTriplet, dmxDotBloomParts, dmxBloomRootActive, dmxBloomHaloSpreadClass, objectToStyle, MATRIX_SIZE } from './core';
    import type { DotMatrixCommonProps, DotMatrixPhase, DotAnimationResolver } from './core';

    interface Props extends DotMatrixCommonProps {
        phase: DotMatrixPhase;
        reducedMotion?: boolean;
        onMouseEnter?: () => void;
        onMouseLeave?: () => void;
        animationResolver?: DotAnimationResolver;
    }

    let {
        size = 24,
        dotSize = 3,
        color = 'currentColor',
        colorPreset,
        speed = 1,
        ariaLabel = 'Loading',
        class: className,
        pattern = 'diamond',
        dotShape = 'circle',
        muted = false,
        bloom = false,
        halo = 0,
        dotClass,
        phase,
        reducedMotion = false,
        onMouseEnter,
        onMouseLeave,
        animationResolver,
        opacityBase,
        opacityMid,
        opacityPeak,
        cellPadding,
        boxSize,
        minSize
    }: Props = $props();

    let safeSpeed = $derived(speed > 0 ? speed : 1);
    let speedScale = $derived(1 / safeSpeed);
    let patternIndexes = $derived(new Set(getPatternIndexes(pattern)));
    let layout = $derived(getMatrix5Layout(size, dotSize, cellPadding));
    let gap = $derived(layout.gap);
    let matrixSpan = $derived(layout.matrixSpan);
    let boxDim = $derived(resolveDmxBoxOuterDim({ boxSize, minSize }));
    let outerDim = $derived(boxDim.outerDim);
    let useWrapper = $derived(boxDim.useWrapper);
    let scale = $derived(useWrapper && matrixSpan > 0 ? outerDim / matrixSpan : 1);
    let center = Math.floor(MATRIX_SIZE / 2);
    let ob = $derived(clamp01Dmx(opacityBase));
    let om = $derived(clamp01Dmx(opacityMid));
    let op = $derived(clamp01Dmx(opacityPeak));
    let unit = $derived(dotSize + gap);
    let tokens = $derived(resolveDmxColorTokens(color, colorPreset));
    
    let dmxVarStyleObj = $derived({
        width: `${matrixSpan}px`,
        height: `${matrixSpan}px`,
        '--dmx-speed': speedScale,
        '--dmx-dot-size': `${dotSize}px`,
        '--dmx-halo-level': halo,
        '--dmx-dot-fill': tokens.dotFill,
        color: tokens.resolvedColor,
        ...(ob !== undefined && { '--dmx-opacity-base': ob }),
        ...(om !== undefined && { '--dmx-opacity-mid': om }),
        ...(op !== undefined && { '--dmx-opacity-peak': op }),
        ...(useWrapper
            ? { transform: `scale(${scale})`, transformOrigin: 'center center' }
            : { minWidth: minSize ? `${minSize}px` : undefined, minHeight: minSize ? `${minSize}px` : undefined })
    });
    
    let dmxVarStyle = $derived(objectToStyle(dmxVarStyleObj));

    let dots = $derived(Array.from({ length: MATRIX_SIZE * MATRIX_SIZE }).map((_, index) => {
        const coords = indexToCoord(index);
        const row = coords.row;
        const col = coords.col;
        const isActive = patternIndexes.has(index);
        const distance = distanceFromCenter(index);
        const angle = polarAngle(index);
        const radiusNormalizedValue = normalizedRadius(index);
        const manhattan = manhattanDistance(index);
        const deltaX = (col - center) * unit;
        const deltaY = (row - center) * unit;

        const animationState = animationResolver
            ? animationResolver({ index, row, col, distanceFromCenter: distance, angleFromCenter: angle, radiusNormalized: radiusNormalizedValue, manhattanDistance: manhattan, phase, isActive, reducedMotion })
            : {};
            
        let resolvedAnimationStyle = animationState.style ? { ...animationState.style } : undefined;
        let isBloomDot = false;
        let stylePatch: any = resolvedAnimationStyle;

        if (isActive) {
            const rawOpacity = stylePatch?.opacity;
            if (stylePatch != null && typeof rawOpacity === 'number') {
                const remappedOpacity = remapOpacityToTriplet(rawOpacity, ob, om, op);
                stylePatch = { ...stylePatch, opacity: remappedOpacity };
                const parts = dmxDotBloomParts(true, rawOpacity, bloom, halo, ob, om, op);
                stylePatch['--dmx-bloom-level'] = parts.level;
                isBloomDot = parts.bloomDot;
            } else {
                const parts = dmxDotBloomParts(true, 0, bloom, halo, ob, om, op);
                if (parts.level > 0) {
                    stylePatch = { ...(stylePatch ?? {}), '--dmx-bloom-level': parts.level };
                }
                isBloomDot = parts.bloomDot;
            }
        }

        const dotStyleObj = {
            width: `${dotSize}px`,
            height: `${dotSize}px`,
            '--dmx-distance': distance,
            '--dmx-row': row,
            '--dmx-col': col,
            '--dmx-x': `${deltaX}px`,
            '--dmx-y': `${deltaY}px`,
            '--dmx-angle': angle,
            '--dmx-radius': radiusNormalizedValue,
            '--dmx-manhattan': manhattan,
            ...stylePatch,
            ...(!isActive ? { opacity: 0, visibility: 'hidden', pointerEvents: 'none', animation: 'none' } : {})
        };
        
        return {
            index,
            isActive,
            isBloomDot,
            className: cx('dmx-dot', !isActive && 'dmx-inactive', isBloomDot && 'dmx-bloom-dot', dotClass, animationState.class),
            style: objectToStyle(dotStyleObj)
        };
    }));
</script>

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
            minWidth: minSize ? `${minSize}px` : undefined,
            minHeight: minSize ? `${minSize}px` : undefined,
            overflow: 'hidden'
        })}
        onmouseenter={onMouseEnter}
        onmouseleave={onMouseLeave}
    >
        <div
            class={cx(
                'dmx-root',
                `dmx-dot-shape-${dotShape}`,
                muted && 'dmx-muted',
                dmxBloomRootActive(bloom, halo) && 'dmx-bloom',
                dmxBloomHaloSpreadClass(halo)
            )}
            style={dmxVarStyle}
        >
            <div class="dmx-grid" style="gap: {gap}px">
                {#each dots as dot (dot.index)}
                    <span aria-hidden="true" class={dot.className} style={dot.style}></span>
                {/each}
            </div>
        </div>
    </div>
{:else}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        role="status"
        aria-live="polite"
        aria-label={ariaLabel}
        class={cx(
            'dmx-root',
            `dmx-dot-shape-${dotShape}`,
            muted && 'dmx-muted',
            dmxBloomRootActive(bloom, halo) && 'dmx-bloom',
            dmxBloomHaloSpreadClass(halo),
            className
        )}
        style={dmxVarStyle}
        onmouseenter={onMouseEnter}
        onmouseleave={onMouseLeave}
    >
        <div class="dmx-grid" style="gap: {gap}px">
            {#each dots as dot (dot.index)}
                <span aria-hidden="true" class={dot.className} style={dot.style}></span>
            {/each}
        </div>
    </div>
{/if}