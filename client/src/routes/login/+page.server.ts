import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.user) return;

	if (locals.user.onboarded) {
		throw redirect(303, '/home');
	}

	throw redirect(303, '/onboarding');
};
