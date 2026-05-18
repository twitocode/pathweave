import type { Actions, PageServerLoad } from './$types.js';
import { fail, redirect } from '@sveltejs/kit';
import { superValidate } from 'sveltekit-superforms';
import { zod4 } from 'sveltekit-superforms/adapters';
import {
	onboardingSchema,
	type OnboardingFormData
} from '$lib/components/onboarding/schema.js';

const defaults: OnboardingFormData = {
	program: '',
	year: '1st Year',
	completedCourses: [],
	wakeUpTime: '',
	bedtime: '19:00',
	onCampus: true,
	lat: 43.2614,
	lng: -79.9198,
	jobInfo: '',
	futurePlans: '',
	professorQuality: 2,
	teachingStyle: 2,
	avoidedCourses: []
};

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
		// Persist onboarding server-side when backend is wired.
		throw redirect(303, '/home');
	}
};
