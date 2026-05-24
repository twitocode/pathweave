<script lang="ts">
	import Button from "$lib/components/ui/button/button.svelte";
	import * as Dialog from '$lib/components/ui/dialog';
	import type { Plan } from '$lib/types';
	import { TrashSimpleIcon } from 'phosphor-svelte';

	type Props = {
		plan: Plan;
	};
	let { plan }: Props = $props();
</script>

<div
	class="relative flex size-90 flex-col border border-primary bg-[#f5f5f0] p-8 dark:bg-secondary"
>
	<a
		href="/plans/{plan.id}"
		class="absolute inset-0 z-0"
		aria-label="Open {plan.title}"
	></a>

	<span class="relative z-10 flex-5 text-5xl text-pretty pointer-events-none">{plan.title}</span>

	<div class="relative z-10 flex items-center justify-between pointer-events-none">
		<span class="font-semibold">{plan.term}</span>
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
					<Dialog.Description>
						This action cannot be undone.
					</Dialog.Description>
				</Dialog.Header>
        <Dialog.Footer class="sm:justify-start">
          <Button class="bg-red-800">
            <TrashSimpleIcon /> Delete
          </Button>
        </Dialog.Footer>
			</Dialog.Content>
		</Dialog.Root>
	</div>
</div>
