<script lang="ts">
	import { COURSES } from '$lib/components/onboarding/constants.js';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { getCourseSectionsByTerm } from '$lib/server-url';
	import { PlanSymbol, type PlanStore } from '$lib/stores/plan.svelte';
	import type { Schedule, TermNumber } from '$lib/types';
	import { cn, getTermString } from '$lib/utils';
	import { getContext } from 'svelte';

	const planStore = getContext<PlanStore>(PlanSymbol);

	let { open = $bindable(false), courseValue = '' } = $props();
	const course = $derived(COURSES.find((c) => c.value === courseValue));
	const courseName = $derived(course?.label.split(': ')[1]);
	const courseCode = $derived(course?.label.split(': ')[0]);

	let sections: Record<string, Schedule[]> = $state({});
	let sectionCount: number = $state(0);
	let terms: string[] = $state([]);

	const restructureData = () => {
		type Result = {
			name: string;
			schedules: Schedule[];
		};
		const output: (Result & { children: Result[] })[] = [];

		const skipped = [];
		for (const [name, schedules] of Object.entries(sections)) {
			if (name.startsWith('LEC') || name.startsWith('SEM')) {
				output.push({
					name,
					schedules,
					children: []
				});
			} else if (name.startsWith('TUT') || name.startsWith('LAB')) {
				const parentName = schedules[0].parent;
				const parent = output.find((x) => x.name == parentName);
				if (!parent) {
					skipped.push({ name, schedules });
					continue;
				}

				parent.children.push({ name, schedules });
			}
		}
		for (const [name, schedules] of Object.entries(sections)) {
			const parentName = schedules[0].parent;
			const parent = output.find((x) => x.name == parentName);
			if (parent) parent.children.push({ name, schedules });
		}

    return output;
	};

	const getCourseInfo = async () => {
		const res = await fetch(getCourseSectionsByTerm(course!.value, planStore.termNumber));
		if (res.ok) {
			const data = await res.json();
			console.log(data);
			sections = data.sections;
			sectionCount = data.count;
			terms = data.terms ?? [];

			console.log(restructureData())
		}
	};

	$effect(() => {
		if (course !== undefined) {
			getCourseInfo();
		}
	});
</script>

<Dialog.Root bind:open>
	<Dialog.Content class={cn({ 'sm:max-w-600': terms.includes(planStore.termString) })}>
		<Dialog.Header>
			<Dialog.Title class="flex flex-col">
				<span class="text-lg font-bold md:text-xl">
					{courseCode || 'Course Details'}
				</span>
				<span class="opacity-75">
					{courseName}
				</span>
			</Dialog.Title>
		</Dialog.Header>
		<div class="py-4">
			{#if sectionCount == 0}
				<div class="flex flex-col gap-2">
					<span> Course is unavailable for this semester </span>
					{#if terms.length > 0}
						<span class="text-lg font-bold"
							>Available in {terms.map(
								(x, i) =>
									getTermString(x as TermNumber) +
									(i < terms.length && terms.length > 1 ? ', ' : '')
							)}</span
						>
					{/if}
				</div>
			{:else}
				{#each Object.entries(sections) as [name, schedules] (name)}
					<div>
						<strong>{name}</strong>
						{#each schedules as schedule (schedule.id)}
							{schedule.instructor}
						{/each}
					</div>
				{/each}
			{/if}
		</div>
		<Dialog.Footer>
			<Button onclick={() => (open = false)}>Close</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
