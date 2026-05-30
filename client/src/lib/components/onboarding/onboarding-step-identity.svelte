<script lang="ts">
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Form from '$lib/components/ui/form/index.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { cn } from '$lib/utils.js';
	import CaretUpDownIcon from 'phosphor-svelte/lib/CaretUpDown';
	import type { Writable } from 'svelte/store';
	import type { SuperForm } from 'sveltekit-superforms';
	import {
		COURSES,
		FIELD_SHELL,
		LABEL_CLASS,
		PROGRAMS,
		YEARS,
		labelForProgram
	} from './constants.js';
	import OnboardingChipsField from './onboarding-chips-field.svelte';
	import type { OnboardingFormData } from './schema.js';

	let {
		form,
		formData
	}: {
		form: SuperForm<OnboardingFormData>;
		formData: Writable<OnboardingFormData>;
	} = $props();

	let draftCompleted = $state('');
	let open = $state(false);
	let searchQuery = $state('');

	const filteredPrograms = $derived(
		PROGRAMS.filter((p) => p.label.toLowerCase().includes(searchQuery.toLowerCase())).slice(0, 5)
	);
</script>

<div class="space-y-10">
	<div class="grid min-w-0 gap-8">
		<Form.Field {form} name="program" class="min-w-0">
			<Form.Control>
				{#snippet children({ props })}
					<Form.Label class={LABEL_CLASS}
						>Program <span class="translate-y-[4px] text-xl font-bold text-brand-red">*</span
						></Form.Label
					>
					<Popover.Root bind:open>
						<Popover.Trigger
							{...props}
							class={cn(
								FIELD_SHELL,
								'mt-2 flex h-auto min-h-10 w-full min-w-0 items-center justify-between py-2'
							)}
						>
							<span class="line-clamp-2 min-w-0 flex-1 text-left leading-snug whitespace-normal">
								{labelForProgram($formData.program)}
							</span>
							<CaretUpDownIcon class="ml-2 size-4 shrink-0 opacity-50" />
						</Popover.Trigger>
						<Popover.Content
							align="start"
							sideOffset={0}
							class="w-(--bits-popover-anchor-width) overflow-hidden rounded-2xl border border-zinc-200 bg-[#f5f5f0] p-0 dark:border-zinc-800 dark:bg-zinc-900"
						>
							<Command.Root shouldFilter={false}>
								<Command.Input placeholder="Search program..." bind:value={searchQuery} />
								<Command.List class="max-h-48 overflow-y-auto">
									<Command.Empty>No program found.</Command.Empty>
									<Command.Group>
										{#each filteredPrograms as p (p.value)}
											<Command.Item
												value={p.label}
												onSelect={() => {
													$formData.program = p.value;
													open = false;
												}}
												class="text-xs"
											>
												<span class="line-clamp-2 leading-snug whitespace-normal">{p.label}</span>
											</Command.Item>
										{/each}
									</Command.Group>
								</Command.List>
							</Command.Root>
						</Popover.Content>
					</Popover.Root>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>

		<Form.Field {form} name="year" class="min-w-0">
			<Form.Control>
				{#snippet children({ props })}
					<Form.Label class={LABEL_CLASS}
						>Year <span class="translate-y-[4px] text-xl font-bold text-brand-red">*</span
						></Form.Label
					>
					<Select.Root type="single" bind:value={$formData.year}>
						<Select.Trigger
							{...props}
							class={cn(FIELD_SHELL, 'mt-2 flex h-10 w-full min-w-0 items-center justify-between')}
						>
							<span class="min-w-0 flex-1 truncate text-left">
								{$formData.year || 'Select'}
							</span>
						</Select.Trigger>
						<Select.Content
							class="border border-zinc-200 bg-[#f5f5f0] dark:border-zinc-800 dark:bg-zinc-900"
						>
							{#each YEARS as y, i (y + i)}
								<Select.Item value={y} label={y} class="text-xs" />
							{/each}
						</Select.Content>
					</Select.Root>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>
	</div>

	<OnboardingChipsField
		label="Completed Courses"
		values={$formData.completedCourses}
		bind:draft={draftCompleted}
		suggestions={COURSES}
		placeholder="Search for a course..."
		chipClass="inline-flex items-center gap-1 border border-zinc-300 bg-zinc-100 px-2 py-0.5 text-[10px] font-bold tracking-[0.1em] uppercase text-zinc-800 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
		normalize={(s) => s.trim().toUpperCase()}
		onAdd={(v) => {
			$formData.completedCourses = [...$formData.completedCourses, v];
		}}
		onRemove={(i) => {
			$formData.completedCourses = $formData.completedCourses.filter((_, idx) => idx !== i);
		}}
	/>
</div>
