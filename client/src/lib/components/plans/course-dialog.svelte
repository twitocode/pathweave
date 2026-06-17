<script lang="ts">
	import { COURSES } from '$lib/components/onboarding/constants.js';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { getCourseSectionsByTerm } from '$lib/server-url';
	import type { Schedule } from '$lib/types';

	let { open = $bindable(false), courseValue = '', term = '' } = $props();
	const course = $derived(COURSES.find((c) => c.value === courseValue));

	let sections: Record<string, Schedule[]> = $state({});
	let sectionCount: number = $state(0);

	$inspect(sections).with(console.log);
	const getCourseInfo = async () => {
		const res = await fetch(getCourseSectionsByTerm(course!.value, term));
		if (res.ok) {
			const data = await res.json();
			sections = data.sections;
			sectionCount = data.count;
		}
	};

	$effect(() => {
		if (course !== undefined) {
			getCourseInfo();
		}
	});
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-106.25">
		<Dialog.Header>
			<Dialog.Title>{course?.label || 'Course Details'}</Dialog.Title>
			<Dialog.Description>
				Here you can see the details for this course and add it to your plan.
			</Dialog.Description>
		</Dialog.Header>
		<div class="py-4">
			{#if course}
				<p class="text-sm">Course value: {course.value}</p>
			{:else}
				<p class="text-sm">No course selected.</p>
			{/if}
			sections: {sectionCount}
			{#each Object.entries(sections) as [name, schedules]}
				<div>
					<strong>{name}</strong>
					{#each schedules as schedule}
						{schedule.instructor}
					{/each}
				</div>
			{/each}
		</div>
		<Dialog.Footer>
			<Button onclick={() => (open = false)}>Close</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
