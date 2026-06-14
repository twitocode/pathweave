<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<main
	class="mx-auto flex min-h-screen max-w-7xl flex-col items-center justify-between py-5 text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />
	{@render children()}
</main>

<footer
	class="w-full border-t border-zinc-200 bg-[#f5f5f0]/80 py-6 backdrop-blur-sm dark:border-zinc-900 dark:bg-zinc-950/80"
>
	<div class="mx-auto max-w-7xl px-6 md:px-12">
		<div class="text-[12px] tracking-[0.2em] text-zinc-600 dark:text-zinc-400">© 2026 PathWeave</div>
	</div>
</footer>
