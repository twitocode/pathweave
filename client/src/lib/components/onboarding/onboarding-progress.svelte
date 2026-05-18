<script lang="ts">
	import { cn } from '$lib/utils.js';

	let { step }: { step: number } = $props();
</script>

<div class="mb-8 flex flex-col items-center gap-3">
	<div class="flex w-full max-w-xs gap-px">
		{#each [1, 2, 3] as s (s)}
			<div
				class={cn(
					'h-1 flex-1 transition-colors',
					s <= step
						? 'bg-zinc-900 dark:bg-zinc-100'
						: 'bg-zinc-300 dark:bg-zinc-700'
				)}
			></div>
		{/each}
	</div>
	<p class="text-[10px] font-bold tracking-[0.2em] uppercase text-zinc-500 dark:text-zinc-400">
		Step {step} of 3
	</p>
</div>
