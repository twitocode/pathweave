<script lang="ts">
	import { STEP_META } from './constants.js';

	let { step }: { step: number } = $props();
</script>

<div class="mb-10 text-center">
	<h1 class="mb-3 text-3xl leading-tight font-bold tracking-tight sm:text-4xl md:text-5xl">
		{STEP_META[step - 1].title}
	</h1>
	<p class="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
		{STEP_META[step - 1].kicker}
	</p>
</div>
