import { z } from 'zod';

export const onboardingSchema = z.object({
	program: z.string().min(1, 'Select a program'),
	year: z.string().min(1, 'Select your year'),
	completedCourses: z.array(z.string()).default([]),
	wakeUpTime: z.string().min(1, 'Select a wake time'),
	bedtime: z.string().min(1, 'Select a bedtime'),
	onCampus: z.boolean().default(true),
	lat: z.number().default(43.2614),
	lng: z.number().default(-79.9198),
	jobInfo: z.string().max(1000, 'Job info cannot exceed 1000 characters').default(''),
	futurePlans: z.string().max(2000, 'Future plans cannot exceed 2000 characters').default(''),
	professorQuality: z.coerce.number().min(1).max(3).default(2),
	teachingStyle: z.coerce.number().min(1).max(3).default(2),
	avoidedCourses: z.array(z.string()).default([])
});

export type OnboardingSchema = typeof onboardingSchema;
export type OnboardingFormData = z.infer<typeof onboardingSchema>;

export const step1Schema = onboardingSchema.pick({
	program: true,
	year: true,
	completedCourses: true
});

export const step2Schema = onboardingSchema.pick({
	wakeUpTime: true,
	bedtime: true,
	onCampus: true,
	lat: true,
	lng: true,
	jobInfo: true,
	futurePlans: true
});
