<script lang="ts">
	import { resolve } from '$app/paths';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import type { Plan } from '$lib/types';
	import { cn, getTermNumber, getTermString } from '$lib/utils';
	import { GraduationCapIcon, TrashSimpleIcon } from 'phosphor-svelte';

	type Props = {
		plan: Plan;
		index: number;
	};
	let { plan, index }: Props = $props();

	

	const term = $derived(getTermString(plan.term));

	const tints = ['bg-purple-200', 'bg-blue-200', 'bg-teal-200', 'bg-rose-200'] as const;
	const tint = $derived(tints[index % tints.length]);
</script>

<div
	class={cn(
		'text-md hover:bg-bg-brand-purple/50 relative flex aspect-square size-full w-full flex-col rounded-2xl bg-secondary p-5 font-medium text-secondary-foreground drop-shadow-xs drop-shadow-[#c5aaf7] transition ease-out text-shadow-xs hover:scale-105 hover:ring-2 hover:ring-[#AE87F7] active:translate-y-0.75 sm:size-90 md:size-70 lg:size-90 dark:drop-shadow-[#a87ff4]'
	)}
>
	<div
		class={cn(
			'absolute inset-0 rounded-2xl opacity-30 mix-blend-multiply dark:mix-blend-screen',
			tint
		)}
		aria-hidden="true"
	></div>

	<a href={resolve(`/plans/${plan.id}`)} class="absolute inset-0 z-0" aria-label="Open {plan.title}"
	></a>

	<div class="flex flex-5 flex-col space-y-4">
		<span class="pointer-events-none relative z-10 text-3xl text-pretty lg:text-4xl"
			>{plan.title}</span
		>
	</div>
	<div class="pointer-events-none relative flex flex-col justify-between gap-2">
		<div class="">
			<span class="flex flex-1 items-center gap-2"
				><GraduationCapIcon /> {plan.courseCount} Courses</span
			>
		</div>
		<div class="flex w-full items-center justify-between">
			<span class="font-semibold text-primary/80">{term}</span>
			<Dialog.Root>
				<Dialog.Trigger
					type="button"
					class="pointer-events-auto relative z-10 inline-flex cursor-pointer hover:scale-125"
				>
					<TrashSimpleIcon />
				</Dialog.Trigger>
				<Dialog.Content>
					<Dialog.Header>
						<Dialog.Title>Are you sure absolutely sure?</Dialog.Title>
						<Dialog.Description>This action cannot be undone.</Dialog.Description>
					</Dialog.Header>
					<Dialog.Footer class="sm:justify-start">
						<Button variant="destructive" size="sm">
							<TrashSimpleIcon /> Delete
						</Button>
					</Dialog.Footer>
				</Dialog.Content>
			</Dialog.Root>
		</div>
	</div>
</div>
