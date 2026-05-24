import { getCsrfTokenHref, getLogoutHref } from '$lib/server-url';
import { redirect, type RequestEvent } from '@sveltejs/kit';

export const load = () => {
	throw redirect(303, '/');
};

export const actions = {
	default: async ({ cookies, request }: RequestEvent) => {
		const cookieHeader = request.headers.get('cookie');
		if (!cookieHeader?.includes('wos_session=')) {
			throw redirect(303, '/');
		}

		const csrfRes = await fetch(getCsrfTokenHref(), {
			headers: { cookie: cookieHeader, accept: 'application/json' }
		});
		if (!csrfRes.ok) {
			throw redirect(303, '/');
		}

		const { csrfToken } = (await csrfRes.json()) as { csrfToken: string };

		const logoutRes = await fetch(getLogoutHref(), {
			method: 'POST',
			headers: {
				cookie: cookieHeader,
				'X-CSRF-Token': csrfToken,
				accept: 'application/json'
			},
			redirect: 'manual'
		});

		cookies.delete('wos_session', { path: '/' });

		const location = logoutRes.headers.get('location');
		throw redirect(303, location ?? '/');
	}
};
