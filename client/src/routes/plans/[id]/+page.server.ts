/* eslint-disable @typescript-eslint/no-explicit-any */
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
			const plan: Plan = {
				id: body.id,
				title: body.title,
				term: body.term,
				createdAt: body.created_at,
				updatedAt: body.updated_at,
				userID: body.user_id,
				courseCount: body.course_count,
				courses: body.courses?.map((c: any) => ({
					id: c.id,
					courseId: c.course_id,
					code: c.code,
					name: c.name,
					description: c.description,
					restrictions: c.restrictions,
					prerequisites: c.prerequisites || [],
					units: c.units,
					types: c.types || [],
					teachers: c.teachers?.map((t: any) => ({
						id: t.id,
						name: t.name,
						avgRating: t.avg_rating,
						avgDifficulty: t.avg_difficulty,
						department: t.department,
						rmpId: t.rmp_id,
						numRatings: t.num_ratings
					})) || [],
					sections: c.sections?.map((s: any) => ({
						id: s.id,
						name: s.name,
						type: s.type,
						term: s.term,
						mode: s.mode,
						isInPerson: s.is_in_person,
						meetings: s.meetings?.map((m: any) => ({
							id: m.id,
							days: m.days,
							startTime: m.start_time,
							endTime: m.end_time,
							building: m.building,
							room: m.room
						})) || [],
						teachers: s.teachers?.map((t: any) => ({
							id: t.id,
							name: t.name,
							avgRating: t.avg_rating,
							avgDifficulty: t.avg_difficulty,
							department: t.department,
							rmpId: t.rmp_id,
							numRatings: t.num_ratings
						})) || []
					})) || []
				})) || []
			};

			return {
				plan
			};
		} else {
			console.error('Could not fetch plan info');
		}
	} catch (err) {
		console.log(err);
	}
};
