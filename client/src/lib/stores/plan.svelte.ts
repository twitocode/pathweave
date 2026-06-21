import type { Plan } from '$lib/types';
import { getTermString } from '$lib/utils';

export const PlanSymbol = Symbol('plan');

export class PlanStore {
	public current = $state<Plan>({
		id: '',
		createdAt: '',
		term: 'Unknown',
		title: '',
		courseCount: 0,
		courses: [],
		updatedAt: '',
		userID: ''
	});

	constructor(initialState?: Plan) {
		if (initialState) this.current = initialState;
	}

	get termNumber() {
		return this.current.term;
	}

	get termString() {
		return getTermString(this.current.term);
	}
}
