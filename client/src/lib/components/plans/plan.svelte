<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import type { Plan } from '$lib/types';
	import { TrashSimpleIcon } from 'phosphor-svelte';

	type Props = {
		plan: Plan;
	};
	let { plan }: Props = $props();
</script>

<div
	class="text-md hover:bg-bg-brand-purple/50 relative flex aspect-square  flex-col rounded-2xl bg-secondary p-5 font-medium text-secondary-foreground drop-shadow-xs drop-shadow-[#c5aaf7] transition ease-out text-shadow-xs hover:scale-105 hover:ring-2 hover:ring-[#AE87F7] active:translate-y-0.75 sm:size-90 md:size-70 lg:size-90 dark:drop-shadow-[#a87ff4] w-full, size-full"
>
	<a href="/plans/{plan.id}" class="absolute inset-0 z-0" aria-label="Open {plan.title}"></a>

	<span class="pointer-events-none relative z-10 flex-5 text-xl sm:text-4xl md:text-4xl lg:text-5xl text-pretty">{plan.title}</span>

	<div class="pointer-events-none relative z-10 flex items-center justify-between">
		<span class="font-semibold text-primary/80">{plan.term}</span>
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
