<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		title,
		description,
		iconAngle,
		children
	}: {
		title: string;
		description: string;
		iconAngle: number;
		children: Snippet;
	} = $props();
</script>

<div class="pw-card">
	<img
		src="/pw-route-icon.svg"
		alt=""
		aria-hidden="true"
		class="pointer-events-none absolute right-6 top-6 z-0 w-12 opacity-80"
		style="color: var(--color-pw-ink); transform: rotate({iconAngle}deg);"
	/>
	<div
		class="pw-display relative z-10 text-[1.6rem] leading-[1.05] tracking-tight sm:text-[1.95rem]"
		style="color: var(--color-pw-ink);"
	>
		{title}
	</div>
	<div
		class="mt-2.5 text-sm leading-relaxed tracking-tight sm:text-base"
		style="color: var(--color-pw-subtle);"
	>
		{description}
	</div>
	<div
		class="mt-auto border-t-2 pt-5"
		style="border-color: var(--color-pw-line-soft);"
	>
		{@render children()}
	</div>
</div>
