import { getPlanInfo } from '$lib/server-url';
import type { Plan } from '$lib/types';
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, params, request }) => {
	if (!locals.user) {
		throw redirect(303, '/login');
	}

	if (!locals.user.onboarded) {
		throw redirect(303, '/onboarding');
	}

	try {
		const cookieHeader = request.headers.get('cookie') ?? '';
		const res = await fetch(getPlanInfo(params.id), {
			headers: {
				cookie: cookieHeader,
				accept: 'application/json'
			}
		});
		const body = await res.json();
		if (res.ok) {
			const plan = body as Plan;

			return {
				plan
			};
		} else {
			console.error('Could not fetch plan info');
			throw redirect(308, '/plans');
		}
	} catch (err) {
		console.log(err);
		throw redirect(308, '/plans');
	}
};
