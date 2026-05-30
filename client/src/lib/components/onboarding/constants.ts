import coursesRaw from '$lib/data/courses.json';
import programsRaw from '$lib/data/programs.json';

export const FIELD_SHELL =
	'rounded-2xl border border-zinc-200 bg-[#f5f5f0] px-3 py-2 text-xs text-zinc-900 transition-colors focus-within:border-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100';

export const LABEL_CLASS =
	'flex items-center gap-1.5 text-[10px] font-bold tracking-[0.2em] uppercase text-zinc-600 dark:text-zinc-400';

export const PROGRAMS = programsRaw.map((p) => ({
	value: p.n,
	label: p.n
}));

export const COURSES = coursesRaw.map((c) => ({
	value: c.c,
	label: `${c.c}: ${c.n}`
}));

export const YEARS = ['1st Year', '2nd Year', '3rd Year', '4th Year', '5th+'] as const;

function pad(n: number) {
	return n.toString().padStart(2, '0');
}

export function buildTimeOptions(): { value: string; label: string }[] {
	const out: { value: string; label: string }[] = [];
	for (let hour = 5; hour <= 23; hour++) {
		for (const minute of [0, 30]) {
			if (hour === 23 && minute === 30) break;
			const value = `${pad(hour)}:${pad(minute)}`;
			const h12 = hour % 12 === 0 ? 12 : hour % 12;
			const ampm = hour < 12 ? 'am' : 'pm';
			const label = `${h12}:${minute === 0 ? '00' : '30'}${ampm}`;
			out.push({ value, label });
		}
	}
	return out;
}

export const TIME_OPTIONS = buildTimeOptions();

export function labelForTime(value: string) {
	return TIME_OPTIONS.find((t) => t.value === value)?.label ?? 'Select';
}

export function labelForProgram(value: string) {
	return PROGRAMS.find((p) => p.value === value)?.label ?? 'Select';
}

export function professorBand(n: number) {
	if (n === 1) return "Doesn't matter";
	if (n === 2) return 'Can be alright';
	return 'Must be perfect';
}

export function teachingStyleBand(n: number) {
	if (n === 1) return 'Traditional';
	if (n === 2) return 'Interactive';
	return 'Engaging';
}

export const STEP_META = [
	{ title: 'Who are You?', kicker: 'Tell us about your program and year.' },
	{ title: 'Your Life', kicker: 'Schedule, work, and what drives you.' },
	{ title: 'Your Learning', kicker: 'Priorities, preferences, and courses to avoid.' }
] as const;
