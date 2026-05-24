import { getUserProgramName } from '$lib/server-url';
import type { Plan } from '$lib/types';
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.user) {
		throw redirect(303, '/login');
	}

	if (!locals.user.onboarded) {
		throw redirect(303, '/onboarding');
	}

	try {
		const res = await fetch(getUserProgramName(), {
			credentials: 'include'
		});

		if (res.ok) {
			const body = await res.json();

			//placeholder
			const plans: Plan[] = [
				{
					id: '12324',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString()
				},
				{
					id: '12234',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString()
				},
				{
					id: '1231',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString()
				},
				{
					id: '12314',
					title: 'If commuting at home',
					term: 'Fall 2026',
					createdAt: new Date(Date.now()).toDateString()
				}
			];

			return {
				programName: body,
				plans
			};
		}
	} catch (err) {
		console.log(err);
	}
};
