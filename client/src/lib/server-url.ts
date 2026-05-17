const DEFAULT_API_ORIGIN = 'http://localhost:8000';

function trimTrailingSlash(value: string): string {
	return value.replace(/\/+$/, '');
}

export function getApiOrigin(): string {
	return trimTrailingSlash(import.meta.env.PUBLIC_API_ORIGIN || DEFAULT_API_ORIGIN);
}

export function getAuthLoginHref(): string {
	return `${getApiOrigin()}/auth/login`;
}

export function getAuthMeHref(): string {
	return `${getApiOrigin()}/auth/me`;
}
