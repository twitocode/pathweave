<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import * as Form from '$lib/components/ui/form/index.js';
	import { ArrowLeft, ArrowRight } from 'phosphor-svelte';

	let {
		step,
		submitting,
		onBack,
		onNext
	}: {
		step: number;
		submitting: boolean;
		onBack: () => void;
		onNext: () => void;
	} = $props();
</script>

<div
	class="mt-12 flex items-center justify-between border-t border-zinc-200 pt-8 dark:border-zinc-800"
>
	<Button
		type="button"
    size="sm"
		variant="ghost"
		onclick={onBack}
	>
		<ArrowLeft class="h-3.5 w-3.5" weight="bold" />
		Back
	</Button>

	{#if step < 3}
		<Button
			type="button"
      size="sm"
			onclick={onNext}
		>
			Next
			<ArrowRight class="h-3.5 w-3.5" weight="bold" />
		</Button>
	{:else}
		<Form.Button
  size="sm"
			disabled={submitting}
		>
			{submitting ? 'Saving…' : 'Finish'}
			<ArrowRight class="h-3.5 w-3.5" weight="bold" />
		</Form.Button>
	{/if}
</div>
