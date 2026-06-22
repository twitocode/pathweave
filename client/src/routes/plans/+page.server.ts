import { getAllPlansHref, getUserProgramNameHref } from '$lib/server-url';
import type { Plan } from '$lib/types';
import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals, request, fetch }) => {
	if (!locals.user) {
		throw redirect(303, '/login');
	}

	if (!locals.user.onboarded) {
		throw redirect(303, '/onboarding');
	}

	try {
		const cookieHeader = request.headers.get('cookie') ?? '';
		const res = await fetch(getAllPlansHref(), {
			headers: {
				cookie: cookieHeader,
				accept: 'application/json'
			}
		});
		const body = await res.json();
		if (res.ok) {
			const res2 = await fetch(getUserProgramNameHref(), {
				headers: {
					cookie: cookieHeader,
					accept: 'application/json'
				}
			});

			if (res2.ok) {
				const plans = (Array.isArray(body) ? body : []) as Plan[];
				const programName = await res2.json();

				return {
					programName,
					plans
				};
			} else {
				console.error('Could not fetch course name');
			}
		} else {
			console.error('could not fetch plans');
		}
	} catch (err) {
		console.log(err);
	}
};

export const actions: Actions = {
	createPlan: async ({ request }) => {
		const cookieHeader = request.headers.get('cookie');
		if (!cookieHeader?.includes('wos_session=')) {
			throw redirect(303, '/login');
		}

		const formData = await request.formData();
		const title = String(formData.get('title') ?? '').trim();
		const term = String(formData.get('term') ?? '').trim();

		if (!title || !term) {
			return fail(400, {
				createPlanError: 'Title and term are required.'
			});
		}

		const res = await fetch(getAllPlansHref(), {
			method: 'POST',
			headers: {
				cookie: cookieHeader,
				accept: 'application/json',
				'content-type': 'application/json'
			},
			body: JSON.stringify({
				title,
				term
			})
		});

		if (!res.ok) {
			return fail(res.status, {
				createPlanError: 'Could not create plan. Please try again.'
			});
		}

		throw redirect(303, '/plans');
	}
};
