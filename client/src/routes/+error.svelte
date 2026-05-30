<script lang="ts">
	import { page } from '$app/state';
	import Navbar from '$lib/components/navbar.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeft, House } from 'phosphor-svelte';

	const isNotFound = $derived(page.status === 404);
	const title = $derived(isNotFound ? 'Page not found' : 'Something went wrong');
	const description = $derived(
		isNotFound
			? "This path doesn't exist or may have moved."
			: (page.error?.message ?? 'An unexpected error occurred. Please try again.')
	);
</script>

<svelte:head>
	<title>{title} | PathWeave</title>
</svelte:head>

<main
	class=" relative flex min-h-screen flex-col text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />

	<section
		class="mx-auto flex max-w-7xl flex-1 flex-col items-center justify-center px-6 py-32 md:px-12"
	>
		<p class="mb-4 font-mono text-xl tracking-[0.3em] text-zinc-500 uppercase dark:text-zinc-400">
			{page.status}
		</p>

		<h1
			class="mb-6 text-center font-gro text-5xl leading-[1.1] font-bold tracking-tight sm:text-6xl md:text-7xl"
		>
			{title}
		</h1>

		<p class="mb-12 max-w-md text-center text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
			{description}
		</p>

		<div class="flex flex-wrap items-center justify-center gap-4">
			<Button href="/" size="sm">
				<House weight="bold" class="h-3.5 w-3.5" />
				Home
			</Button>

			{#if page.data.user}
				<Button href="/plans" variant="outline" size="sm">
					<ArrowLeft weight="bold" class="h-3.5 w-3.5" />
					Plans
				</Button>
			{/if}
		</div>
	</section>

	<footer
		class="w-full border-t border-zinc-200 bg-[#f5f5f0]/80 py-6 backdrop-blur-sm dark:border-zinc-900 dark:bg-zinc-950/80"
	>
		<div class="mx-auto max-w-7xl px-6 md:px-12">
			<div class="text-[12px] tracking-[0.2em] text-zinc-600 dark:text-zinc-400">
				© 2026 PathWeave
			</div>
		</div>
	</footer>
</main>
