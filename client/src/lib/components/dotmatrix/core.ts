export type MatrixPattern = 'diamond' | 'full' | 'outline' | 'rose' | 'cross' | 'rings';
export type DotShape = 'circle' | 'square' | 'diamond' | 'hearts';
export type DotMatrixPhase = 'idle' | 'collapse' | 'hoverRipple' | 'loadingRipple';
export type DotMatrixColorPreset =
	| 'solid-theme'
	| 'solid-mint'
	| 'grad-sunset'
	| 'grad-ocean'
	| 'grad-neon'
	| 'grad-aurora'
	| 'grad-fire'
	| 'grad-prism';

const DOT_MATRIX_COLOR_PRESETS: Record<
	DotMatrixColorPreset,
	{ fill: string; glow: string }
> = {
	'solid-theme': { fill: 'var(--color-dot-on)', glow: 'var(--color-dot-on)' },
	'solid-mint': { fill: '#34d399', glow: '#34d399' },
	'grad-sunset': { fill: 'linear-gradient(135deg, #ff5f6d 0%, #ffc371 52%, #ffe29a 100%)', glow: '#ff8b73' },
	'grad-ocean': { fill: 'linear-gradient(140deg, #00c6ff 0%, #0072ff 48%, #4facfe 100%)', glow: '#2f8fff' },
	'grad-neon': { fill: 'linear-gradient(145deg, #b4ff39 0%, #39ffb6 46%, #00d4ff 100%)', glow: '#59ffc8' },
	'grad-aurora': { fill: 'linear-gradient(145deg, #ff3cac 0%, #784ba0 45%, #2b86c5 100%)', glow: '#9c64bf' },
	'grad-fire': { fill: 'linear-gradient(145deg, #ff512f 0%, #dd2476 45%, #ffb347 100%)', glow: '#f96a5f' },
	'grad-prism': { fill: 'linear-gradient(145deg, #12c2e9 0%, #c471ed 45%, #f64f59 100%)', glow: '#9e7de8' }
};

export function resolveDmxColorTokens(color: string, colorPreset?: DotMatrixColorPreset): { resolvedColor: string; dotFill: string } {
	if (!colorPreset || !DOT_MATRIX_COLOR_PRESETS[colorPreset]) {
		return { resolvedColor: color, dotFill: color };
	}
	const preset = DOT_MATRIX_COLOR_PRESETS[colorPreset];
	return { resolvedColor: preset.glow, dotFill: preset.fill };
}

export interface DotMatrixCommonProps {
	size?: number;
	dotSize?: number;
	color?: string;
	colorPreset?: DotMatrixColorPreset;
	speed?: number;
	ariaLabel?: string;
	class?: string;
	pattern?: MatrixPattern;
	muted?: boolean;
	bloom?: boolean;
	halo?: number;
	animated?: boolean;
	hoverAnimated?: boolean;
	dotClass?: string;
	dotShape?: DotShape;
	opacityBase?: number;
	opacityMid?: number;
	opacityPeak?: number;
	cellPadding?: number;
	boxSize?: number;
	minSize?: number;
}

export interface DotAnimationContext {
	index: number;
	row: number;
	col: number;
	distanceFromCenter: number;
	angleFromCenter: number;
	radiusNormalized: number;
	manhattanDistance: number;
	phase: DotMatrixPhase;
	isActive: boolean;
	reducedMotion: boolean;
}

export interface DotAnimationState {
	class?: string;
	style?: Record<string, any>;
}

export type DotAnimationResolver = (ctx: DotAnimationContext) => DotAnimationState;

export function cx(...values: Array<string | undefined | null | false>): string {
	return values.filter(Boolean).join(' ');
}

export const MATRIX_SIZE = 5;
const CENTER = Math.floor(MATRIX_SIZE / 2);
const RANGE = Array.from({ length: MATRIX_SIZE }, (_, index) => index);
const MAX_RADIUS = Math.hypot(CENTER, CENTER);

export function rowMajorIndex(row: number, col: number): number {
	return row * MATRIX_SIZE + col;
}

export function indexToCoord(index: number): { row: number; col: number } {
	return { row: Math.floor(index / MATRIX_SIZE), col: index % MATRIX_SIZE };
}

export const FULL_INDEXES = RANGE.flatMap((row) => RANGE.map((col) => rowMajorIndex(row, col)));

export const DIAMOND_INDEXES = FULL_INDEXES.filter((index) => {
	const { row, col } = indexToCoord(index);
	return Math.abs(row - CENTER) + Math.abs(col - CENTER) <= 2;
});

export const OUTLINE_INDEXES = FULL_INDEXES.filter((index) => {
	const { row, col } = indexToCoord(index);
	return row === 0 || row === MATRIX_SIZE - 1 || col === 0 || col === MATRIX_SIZE - 1;
});

export const CROSS_INDEXES = FULL_INDEXES.filter((index) => {
	const { row, col } = indexToCoord(index);
	return row === CENTER || col === CENTER;
});

export const RINGS_INDEXES = FULL_INDEXES.filter((index) => {
	const { row, col } = indexToCoord(index);
	const radius = Math.hypot(row - CENTER, col - CENTER);
	return Math.round(radius) === 1 || Math.round(radius) === 2;
});

export const ROSE_INDEXES = FULL_INDEXES.filter((index) => {
	const { row, col } = indexToCoord(index);
	const dx = col - CENTER;
	const dy = row - CENTER;
	const angle = Math.atan2(dy, dx);
	const radius = Math.hypot(dx, dy);
	const rose = Math.abs(Math.sin(3 * angle));
	return rose > 0.6 && radius >= 1;
});

const PATTERN_INDEXES: Record<MatrixPattern, number[]> = {
	diamond: DIAMOND_INDEXES,
	full: FULL_INDEXES,
	outline: OUTLINE_INDEXES,
	rose: ROSE_INDEXES,
	cross: CROSS_INDEXES,
	rings: RINGS_INDEXES
};

export function getPatternIndexes(pattern: MatrixPattern = 'diamond'): number[] {
	return PATTERN_INDEXES[pattern];
}

export function distanceFromCenter(index: number): number {
	const { row, col } = indexToCoord(index);
	return Math.hypot(row - CENTER, col - CENTER);
}

export function polarAngle(index: number): number {
	const { row, col } = indexToCoord(index);
	return Math.atan2(row - CENTER, col - CENTER);
}

export function normalizedRadius(index: number): number {
	const { row, col } = indexToCoord(index);
	return Math.hypot(row - CENTER, col - CENTER) / MAX_RADIUS;
}

export function manhattanDistance(index: number): number {
	const { row, col } = indexToCoord(index);
	return Math.abs(row - CENTER) + Math.abs(col - CENTER);
}

export function stylePx(n: number): string {
	return `${n}px`;
}

export function styleOpacity(opacity: number): number {
	return Math.round(opacity * 1e6) / 1e6;
}

const SOURCE_BASE_OPACITY = 0.08;
const SOURCE_MID_OPACITY = 0.34;
const SOURCE_PEAK_OPACITY = 0.94;

function lerpDmx(start: number, end: number, progress: number): number {
	return start + (end - start) * progress;
}

function normalizeProgressDmx(value: number, start: number, end: number): number {
	const span = end - start;
	if (Math.abs(span) < Number.EPSILON) return 0;
	return Math.min(1, Math.max(0, (value - start) / span));
}

function coerceOpacityDmx(value: number | undefined): number | undefined {
	if (value == null || !Number.isFinite(value)) return undefined;
	return Math.min(1, Math.max(0, value));
}

export function remapOpacityToTriplet(
	opacity: number,
	opacityBase: number | undefined,
	opacityMid: number | undefined,
	opacityPeak: number | undefined
): number {
	if (!Number.isFinite(opacity)) return opacity;

	const hasOverrides = opacityBase !== undefined || opacityMid !== undefined || opacityPeak !== undefined;
	const safeOpacity = Math.min(1, Math.max(0, opacity));
	if (!hasOverrides) return safeOpacity;

	const targetBase = coerceOpacityDmx(opacityBase) ?? SOURCE_BASE_OPACITY;
	const targetMid = coerceOpacityDmx(opacityMid) ?? SOURCE_MID_OPACITY;
	const targetPeak = coerceOpacityDmx(opacityPeak) ?? SOURCE_PEAK_OPACITY;

	if (safeOpacity <= SOURCE_BASE_OPACITY) {
		const progress = normalizeProgressDmx(safeOpacity, 0, SOURCE_BASE_OPACITY);
		return Math.min(1, Math.max(0, lerpDmx(0, targetBase, progress)));
	}

	if (safeOpacity <= SOURCE_MID_OPACITY) {
		const progress = normalizeProgressDmx(safeOpacity, SOURCE_BASE_OPACITY, SOURCE_MID_OPACITY);
		return Math.min(1, Math.max(0, lerpDmx(targetBase, targetMid, progress)));
	}

	if (safeOpacity <= SOURCE_PEAK_OPACITY) {
		const progress = normalizeProgressDmx(safeOpacity, SOURCE_MID_OPACITY, SOURCE_PEAK_OPACITY);
		return Math.min(1, Math.max(0, lerpDmx(targetMid, targetPeak, progress)));
	}

	const progress = normalizeProgressDmx(safeOpacity, SOURCE_PEAK_OPACITY, 1);
	return Math.min(1, Math.max(0, lerpDmx(targetPeak, 1, progress)));
}

export const DMX_BLOOM_OPACITY_MIN = 0.6;

export function opacityToBloomLevel(remappedOpacity: number): number {
	return Math.max(0, Math.min(1, (remappedOpacity - DMX_BLOOM_OPACITY_MIN) / (1 - DMX_BLOOM_OPACITY_MIN)));
}

export function remappedOpacityQualifiesForBloom(remappedOpacity: number): boolean {
	return remappedOpacity >= DMX_BLOOM_OPACITY_MIN;
}

export function clampHalo(value: number | undefined): number {
	if (value == null || !Number.isFinite(value)) return 0;
	return Math.min(1, Math.max(0, value));
}

export function dmxBloomRootActive(bloom: boolean, halo: number | undefined): boolean {
	return bloom || clampHalo(halo) > 0;
}

export function dmxBloomHaloSpreadClass(halo: number | undefined): 'dmx-bloom-halo' | false {
	return clampHalo(halo) > 0 ? 'dmx-bloom-halo' : false;
}

export function dmxDotBloomParts(
	isActive: boolean,
	curveOpacity: number,
	bloom: boolean,
	halo: number | undefined,
	ob: number | undefined,
	om: number | undefined,
	op: number | undefined
): { level: number; bloomDot: boolean } {
	const haloN = clampHalo(halo);
	if (!isActive) return { level: 0, bloomDot: false };
	const remapped = remapOpacityToTriplet(curveOpacity, ob, om, op);
	const fromBloom = bloom ? opacityToBloomLevel(remapped) : 0;
	return {
		level: fromBloom,
		bloomDot: haloN > 0 || (bloom && remappedOpacityQualifiesForBloom(remapped))
	};
}

export function getMatrix5Layout(size: number, dotSize: number, cellPadding?: number): { gap: number; matrixSpan: number } {
	const n = MATRIX_SIZE;
	if (cellPadding != null) {
		const g = Math.max(0, cellPadding);
		const matrixSpan = dotSize * n + g * (n - 1);
		return { gap: g, matrixSpan };
	}
	const g = Math.max(1, Math.floor((size - dotSize * n) / (n - 1)));
	return { gap: g, matrixSpan: size };
}

export function resolveDmxBoxOuterDim(options: { boxSize?: number; minSize?: number } | null | undefined): { outerDim: number; useWrapper: boolean } {
	const b = options?.boxSize;
	const hasBox = b != null && b > 0 && Number.isFinite(b);
	if (!hasBox) return { outerDim: 0, useWrapper: false };
	const m = options?.minSize;
	if (m != null && m > 0 && Number.isFinite(m)) {
		return { outerDim: Math.max(b, m), useWrapper: true };
	}
	return { outerDim: b, useWrapper: true };
}

export function clamp01Dmx(n: number | undefined) {
	if (n == null) return undefined;
	if (!Number.isFinite(n)) return undefined;
	return Math.min(1, Math.max(0, n));
}

export function objectToStyle(obj: Record<string, any> | undefined): string {
    if (!obj) return '';
    return Object.entries(obj)
        .filter(([_, v]) => v !== undefined && v !== null)
        .map(([k, v]) => `${k.startsWith('--') ? k : k.replace(/[A-Z]/g, m => '-' + m.toLowerCase())}: ${v}`)
        .join('; ');
}
