<script lang="ts">
	import { COURSES } from '$lib/components/onboarding/constants.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import { cn } from '$lib/utils.js';
	import CaretUpDownIcon from 'phosphor-svelte/lib/CaretUpDown';
	import CourseDialog from './course-dialog.svelte';

	let { term = '' } = $props();

	let open = $state(false);
	let searchQuery = $state('');
	let selectedCourseValue = $state('');
	let dialogOpen = $state(false);

	const filteredCourses = $derived(
		COURSES.filter((c) => c.label.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 5)
	);
</script>

<div class="mb-4 w-full">
	<Popover.Root bind:open>
		<Popover.Trigger
			class={cn(
				'rounded-2xl border border-zinc-200 bg-[#f5f5f0] px-3 py-2 text-xs text-zinc-900 transition-colors focus-within:border-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100',
				'flex h-auto min-h-10 w-full items-center justify-between py-2'
			)}
		>
			<span class="line-clamp-2 min-w-0 flex-1 text-left leading-snug whitespace-normal">
				Search for a course to add...
			</span>
			<CaretUpDownIcon class="ml-2 size-4 shrink-0 opacity-50" />
		</Popover.Trigger>
		<Popover.Content
			align="start"
			sideOffset={0}
			class="w-75 overflow-hidden rounded-2xl border border-zinc-200 bg-[#f5f5f0] p-0 dark:border-zinc-800 dark:bg-zinc-900"
		>
			<Command.Root shouldFilter={false}>
				<Command.Input placeholder="Search course..." bind:value={searchQuery} />
				<Command.List class="max-h-48 overflow-y-auto">
					<Command.Empty>No course found.</Command.Empty>
					<Command.Group>
						{#each filteredCourses as c (c.value)}
							<Command.Item
								value={c.label}
								onSelect={() => {
									selectedCourseValue = c.value;
									open = false;
									dialogOpen = true;
								}}
								class="text-xs"
							>
								<span class="line-clamp-2 leading-snug whitespace-normal">{c.label}</span>
							</Command.Item>
						{/each}
					</Command.Group>
				</Command.List>
			</Command.Root>
		</Popover.Content>
	</Popover.Root>
</div>

<CourseDialog bind:open={dialogOpen} courseValue={selectedCourseValue} {term} />
