import { onboardingSchema } from '$lib/components/onboarding/schema.js';
import { getApiOrigin } from '$lib/server-url';
import { fail, redirect } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod4 } from 'sveltekit-superforms/adapters';
import type { Actions, PageServerLoad } from './$types.js';

export const load: PageServerLoad = async () => {
	return {
		form: await superValidate(zod4(onboardingSchema))
	};
};

export const actions: Actions = {
	default: async (event) => {
		const form = await superValidate(event, zod4(onboardingSchema));
		if (!form.valid) {
			return fail(400, { form });
		}

		console.log('submitting form');
		const cookieHeader = event.request.headers.get('cookie');
		const payload = {
			...form.data,
			year: parseInt(form.data.year[0])
		};

		const res = await fetch(`${getApiOrigin()}/onboarding`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				cookie: cookieHeader || ''
			},
			body: JSON.stringify(payload)
		});

		if (res.ok) {
			throw redirect(303, '/plans');
		} else {
			const data = await res.json();
			if (data?.message === 'onboarding_failed') {
				// TODO: return "Something happened on our end with onboarding"
			}

			// TODO return "Something happened on our end"
		}
	}
};
