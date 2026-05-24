<script lang="ts">
	import { page } from '$app/state';
	import Navbar from '$lib/components/navbar.svelte';
	import * as Button from '$lib/components/ui/button';
	import { ArrowLeft, House } from 'phosphor-svelte';

	let scrollY = $state(0);
	let isScrolled = $derived(scrollY > 50);

	const isNotFound = $derived(page.status === 404);
	const title = $derived(isNotFound ? 'Page not found' : 'Something went wrong');
	const description = $derived(
		isNotFound
			? "This path doesn't exist or may have moved."
			: (page.error?.message ?? 'An unexpected error occurred. Please try again.')
	);
</script>

<svelte:window bind:scrollY />

<svelte:head>
	<title>{title} | PathWeave</title>
</svelte:head>

<main
	class="dotmatrix-bg relative flex min-h-screen flex-col text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar {isScrolled} />

	<section
		class="mx-auto flex max-w-7xl flex-1 flex-col items-center justify-center px-6 py-32 md:px-12"
	>
		<p class="mb-4 font-mono text-xl tracking-[0.3em] text-zinc-500 uppercase dark:text-zinc-400">
			{page.status}
		</p>

		<h1
			class="mb-6 text-center font-geist-pixel text-5xl leading-[1.1] font-bold tracking-tight sm:text-6xl md:text-7xl"
		>
			{title}
		</h1>

		<p class="mb-12 max-w-md text-center text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
			{description}
		</p>

		<div class="flex flex-wrap items-center justify-center gap-4">
			<Button.Root
				href="/"
				class="inline-flex h-12 items-center gap-3 rounded-none border-2 border-zinc-900 bg-zinc-900 px-8 text-xs font-bold tracking-[0.2em] text-white uppercase transition-all hover:bg-zinc-800 dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
			>
				<House weight="bold" class="h-3.5 w-3.5" />
				Home
			</Button.Root>

			{#if page.data.user}
				<Button.Root
					href="/plans"
					variant="outline"
					class="inline-flex h-12 items-center gap-3 rounded-none border-2 border-zinc-300 bg-transparent px-8 text-xs font-bold tracking-[0.2em] text-zinc-900 uppercase transition-all hover:border-zinc-900 dark:border-zinc-700 dark:text-zinc-100 dark:hover:border-zinc-100"
				>
					<ArrowLeft weight="bold" class="h-3.5 w-3.5" />
					Plans
				</Button.Root>
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
