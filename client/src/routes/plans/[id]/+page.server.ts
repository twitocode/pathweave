import type { Plan } from '$lib/types';
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, params }) => {
	if (!locals.user) {
		throw redirect(303, '/login');
	}

	if (!locals.user.onboarded) {
		throw redirect(303, '/onboarding');
	}

	try {
		// const res = await fetch(getPlanHref(params.id), {
		// 	credentials: 'include'
		// });

		const res = {
			ok: true
		};
		if (res.ok) {
			// let body = await res.json();
			//placeholder
			const plans: Plan[] = [
				{
					id: '12324',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString(),
					courseCount: 4,
					userID: '019e33a5-9ba7-77c0-a39b-6edb0a84f879'
				},
				{
					id: '12234',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString(),
					courseCount: 3,
					userID: '019e0dfb-6f64-7c55-99a3-5bb91753e755'
				},
				{
					id: '1231',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString(),
					courseCount: 5,
					userID: '019e0dfb-6f64-7c55-99a3-5bb91753e752'
				},
				{
					id: '12314',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString(),
					courseCount: 3,
					userID: '019e33a5-9ba7-77c0-a39b-6edb0a84f879'
				}
			];

			const body = plans.find((x) => x.id === params.id);
			console.log(body, locals.user);
			if (body?.userID !== locals.user.id) {
				throw redirect(303, '/plans');
			}

			return {
				programName: body,
				plans
			};
		}
	} catch (err) {
		console.log(err);
	}
};
