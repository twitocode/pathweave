<script lang="ts">
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

<div class="mt-12 flex items-center justify-between border-t border-zinc-200 pt-8 dark:border-zinc-800">
	<button
		type="button"
		class="inline-flex items-center gap-2 text-xs font-bold tracking-[0.15em] uppercase text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
		onclick={onBack}
	>
		<ArrowLeft class="h-3.5 w-3.5" weight="bold" />
		Back
	</button>

	{#if step < 3}
		<button
			type="button"
			class="inline-flex h-10 items-center gap-3 border-2 border-zinc-900 bg-zinc-900 px-6 text-xs font-bold tracking-[0.15em] uppercase text-white transition-all hover:bg-zinc-800 dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
			onclick={onNext}
		>
			Next
			<ArrowRight class="h-3.5 w-3.5" weight="bold" />
		</button>
	{:else}
		<Form.Button
			class="inline-flex h-10 items-center gap-3 border-2 border-zinc-900 bg-zinc-900 px-6 text-xs font-bold tracking-[0.15em] uppercase text-white transition-all hover:bg-zinc-800 dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
			disabled={submitting}
		>
			{submitting ? 'Saving…' : 'Finish'}
			<ArrowRight class="h-3.5 w-3.5" weight="bold" />
		</Form.Button>
	{/if}
</div>
