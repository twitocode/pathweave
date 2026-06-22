<script lang="ts">
	import { COURSES } from '$lib/components/onboarding/constants.js';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { getCourseSectionsByTerm } from '$lib/server-url';
	import { getPlanStore } from '$lib/stores/plan.svelte';
	import type { Schedule, TermNumber } from '$lib/types';
	import { cn, getTermString } from '$lib/utils';

	const planStore = getPlanStore();

	let { open = $bindable(false), courseValue = '' } = $props();
	const course = $derived(COURSES.find((c) => c.value === courseValue));
	const courseName = $derived(course?.label.split(': ')[1]);
	const courseCode = $derived(course?.label.split(': ')[0]);

	let sections: Record<string, Schedule[]> = $state({});
	let sectionCount: number = $state(0);
	let terms: string[] = $state([]);
	let selectedParent: string | null = $state(null);

	const restructuredData = $derived.by(() => {
		type Result = {
			name: string;
			schedules: Schedule[];
		};
		const output: (Result & { children: Result[] })[] = [];
		const childrenList: Result[] = [];

		for (const [name, schedules] of Object.entries(sections)) {
			if (name.startsWith('LEC') || name.startsWith('SEM')) {
				output.push({ name, schedules, children: [] });
			} else {
				childrenList.push({ name, schedules });
			}
		}

		for (const child of childrenList) {
			const parentNames = child.schedules[0]?.parents || [];
			let hasValidParent = false;
			for (const parentName of parentNames) {
				const parent = output.find((x) => x.name === parentName);
				if (parent) {
					parent.children.push(child);
					hasValidParent = true;
				}
			}
			if (!hasValidParent) {
				// If a child has no valid parent, promote it to top-level
				output.push({ ...child, children: [] });
			}
		}

		return output;
	});

	const getCourseInfo = async () => {
		const res = await fetch(getCourseSectionsByTerm(course!.value, planStore.termNumber));
		if (res.ok) {
			const data = await res.json();
			sections = data.sections;
			sectionCount = data.count;
			terms = data.terms ?? [];
			selectedParent = null; // Reset selection on load
		}
	};

	$effect(() => {
		if (course !== undefined) {
			getCourseInfo();
		}
	});
</script>

<Dialog.Root bind:open>
	<Dialog.Content class={cn('w-1/2 sm:max-w-600')}>
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
		<div class="min-h-[40vh] py-4">
			{#if sectionCount === 0}
				<div class="flex flex-col gap-2">
					<span> Course is unavailable for this semester </span>
					{#if terms.length > 0}
						<span class="text-lg font-bold"
							>Available in {terms
								.map((x, i) => getTermString(x as TermNumber) + (i < terms.length - 1 ? ', ' : ''))
								.join('')}</span
						>
					{/if}
				</div>
			{:else}
				<div class="flex h-full w-full flex-row gap-4">
					<!-- Parent Sections Column -->
					<div class="flex w-1/2 flex-col gap-2 border-r pr-4">
					
						<div class="flex max-h-[50vh] flex-col gap-2 overflow-y-auto p-2">
							{#each restructuredData as parent, i (parent.name)}
								<button
									class="flex flex-col rounded-md border p-3 text-left transition-colors hover:bg-accent hover:text-accent-foreground focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:outline-none"
									class:bg-accent={selectedParent === parent.name}
									class:border-primary={selectedParent === parent.name}
									onclick={() => (selectedParent = parent.name)}
								>
									<strong class="text-sm">{parent.name}</strong>
									<span class="text-xs text-muted-foreground">
										{parent.schedules[0]?.instructor || 'No Specific Professor'}
									</span>
								</button>
							{/each}
						</div>
					</div>

					<!-- Child Sections Column -->
					<div class="flex w-1/2 flex-col gap-2 p-2">
					
						<div class="flex max-h-[50vh] flex-col gap-2 overflow-y-auto pr-2">
							{#if selectedParent}
								{@const activeParent = restructuredData.find((p) => p.name === selectedParent)}
								{#if activeParent && activeParent.children.length > 0}
									{#each activeParent.children as child (child.name)}
										<div class="flex flex-col rounded-md border bg-card p-3">
											<strong class="text-sm">{child.name}</strong>
											<span class="text-xs text-muted-foreground">
												{child.schedules[0]?.instructor || 'Staff'}
											</span>
										</div>
									{/each}
								{:else}
									<div
										class="flex h-32 items-center justify-center rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground"
									>
										No tutorials or labs for this section.
									</div>
								{/if}
							{:else}
								<div
									class="flex h-32 items-center justify-center rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground"
								>
									Select a lecture or seminar to view its components.
								</div>
							{/if}
						</div>
					</div>
				</div>
			{/if}
		</div>
		<Dialog.Footer>
			<Button onclick={() => (open = false)}>Close</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
