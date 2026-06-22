import type { Plan } from '$lib/types';
import { getTermString } from '$lib/utils';
import { getContext, setContext } from 'svelte';

const PlanStoreKey = Symbol('plan-store');

export class PlanStore {
	public current = $state<Plan>({
		id: '',
		createdAt: '',
		term: 'Unknown',
		title: '',
		courseCount: 0,
		courses: [],
		updatedAt: '',
		userId: ''
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

export function getPlanStore(): PlanStore {
	return getContext(PlanStoreKey);
}

export function setPlanStore(initialData?: Plan) {
	const store = new PlanStore(initialData);
	setContext(PlanStoreKey, store);
}
