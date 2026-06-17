import type { TermNumber, TermString } from '$lib/types';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, 'child'> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, 'children'> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export function getTermString(t: TermNumber): string {
	const term = {
		'2259': 'Fall 2025',
		'2261': 'Winter 2026',
		'2265': 'Spring/Summer 2026',
		'2269': 'Fall 2026',
		'2271': 'Winter 2027',
		'2275': 'Spring/Summer 2027',
		Unknown: 'Unknown'
	}[t];

	if (term === undefined) return 'Invalid Term';
	return term;
}

export function getTermNumber(t: TermString): string {
	const term = {
		'Fall 2025': '2259',
		'Winter 2026': '2261',
		'Spring/Summer 2026': '2265',
		'Fall 2026': '2269',
		'Winter 2027': '2271',
		'Spring/Summer 2027': '2275',
		Unknown: 'Unknown'
	}[t];

	if (term === undefined) return 'Invalid Term';
	return term;
}
