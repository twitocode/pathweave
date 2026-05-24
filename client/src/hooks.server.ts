import { getAuthMeHref } from '$lib/server-url';
import { isRedirect, redirect, type Handle } from '@sveltejs/kit';

type AuthUser = {
	id: string;
	email: string;
	onboarded: boolean;
};

type AuthMeResponse = {
	id?: unknown;
	email?: unknown;
	onboarded?: unknown;
	user?: {
		id?: unknown;
		email?: unknown;
		onboarded?: unknown;
	};
};

function toAuthUser(payload: AuthMeResponse): AuthUser | null {
	const user = payload.user ?? payload;
	if (typeof user?.id !== 'string' || typeof user?.email !== 'string') {
		return null;
	}

	return {
		id: user.id,
		email: user.email,
		onboarded: !!user.onboarded
	};
}

export const handle: Handle = async ({ event, resolve }) => {
	event.locals.user = null;

	const routeId = event.route.id || '';
	const isAuthRoute = routeId.startsWith('/auth');
	const isOnboardingRoute = routeId === '/onboarding';
	const isLoginRoute = routeId === '/login';

	// 1. Check for forced onboarding from query param (e.g. from callback)
	const hasOnboardedParam = event.url.searchParams.get('onboarded');
	if (hasOnboardedParam === 'false' && !isOnboardingRoute) {
		throw redirect(303, '/onboarding');
	}

	const cookieHeader = event.request.headers.get('cookie');
	if (!cookieHeader || !cookieHeader.includes('wos_session=')) {
		return resolve(event);
	}

	try {
		const response = await event.fetch(getAuthMeHref(), {
			method: 'GET',
			headers: {
				cookie: cookieHeader,
				accept: 'application/json'
			}
		});

		if (response.ok) {
			const body = (await response.json()) as AuthMeResponse;
			const user = toAuthUser(body);
			event.locals.user = user;

			if (user) {
				if (isLoginRoute) {
					throw redirect(303, user.onboarded ? '/plans' : '/onboarding');
				}

				if (!user.onboarded && !isOnboardingRoute && !isAuthRoute) {
					throw redirect(303, '/onboarding');
				}

				if (user.onboarded && isOnboardingRoute) {
					throw redirect(303, '/plans');
				}
			}
		}
	} catch (e) {
		if (isRedirect(e)) {
			throw e;
		}
		// If the backend is unavailable or other errors, continue as an anonymous session.
		event.locals.user = null;
	}

	return resolve(event);
};
