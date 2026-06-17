<script lang="ts">
	import { COURSES } from '$lib/components/onboarding/constants.js';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { getCourseSectionsByTerm } from '$lib/server-url';
	import type { Schedule, TermNumber } from '$lib/types';
	import { cn, getTermString } from '$lib/utils';

	let { open = $bindable(false), courseValue = '', term = '' } = $props();
	const course = $derived(COURSES.find((c) => c.value === courseValue));

	let sections: Record<string, Schedule[]> = $state({});
	let sectionCount: number = $state(0);
	let terms: string[] = $state([]);

  const restructureData = () => {
    
  }

	const getCourseInfo = async () => {
		const res = await fetch(getCourseSectionsByTerm(course!.value, term));
		if (res.ok) {
			const data = await res.json();
			console.log(data);
			sections = data.sections;
			sectionCount = data.count;
			terms = data.terms ?? [];
		}
	};

	$effect(() => {
		if (course !== undefined) {
			getCourseInfo();
		}
	});
</script>

<Dialog.Root bind:open>
	<Dialog.Content class={cn({ 'sm:max-w-500':  terms.includes(term) })}>
		<Dialog.Header>
			<Dialog.Title class="font-bold text-lg md:text-xl">{course?.label || 'Course Details'}</Dialog.Title>
			<Dialog.Description>
				See the details for this course and add it to your plan.
			</Dialog.Description>
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
				{#each Object.entries(sections) as [name, schedules]}
					<div>
						<strong>{name}</strong>
						{#each schedules as schedule}
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
