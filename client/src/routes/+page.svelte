<script lang="ts">
	import { resolve } from '$app/paths';
	import Navbar from '$lib/components/navbar.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowRight } from 'phosphor-svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<svelte:head>
	<title>PathWeave - Smart Course Planning for McMaster</title>
</svelte:head>

<main
	class=" relative min-h-screen text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />

	<!-- Hero -->
	<section
		class="mx-auto flex min-h-[70vh] mt-20 max-w-7xl flex-col items-center justify-center px-6 md:px-12"
	>
		<div class="max-w-3xl text-center font-gro">
			<h1 class="mb-8 text-5xl leading-[1.1] font-bold sm:text-7xl md:text-9xl">
				<span class="">Your schedule</span>,<br />
				<span class="text-brand-purple">optimized.</span>
			</h1>

			<p
				class="mx-auto mb-12 max-w-lg text-sm leading-relaxed text-zinc-900 md:text-base dark:text-zinc-300"
			>
				Figure out what <span class="font-bold italic">McMaster</span> course schedule is right for your
				depending on your future goals, job schedule, professor ratings, and more.
			</p>

			{#if data.user?.onboarded}
				<Button href="/plans">
					Go to Plans
					<ArrowRight weight="bold" class="h-3.5 w-3.5" />
				</Button>
			{:else if data.user}
				<Button href="/onboarding">
					Continue Onboarding
					<ArrowRight weight="bold" class="h-3.5 w-3.5" />
				</Button>
			{:else}
				<Button href="/login" size="lg">
					Start Planning
					<ArrowRight weight="bold" class="h-3.5 w-3.5" />
				</Button>
			{/if}
		</div>
	</section>

	<!-- Value pillars -->
	<section class="mx-auto max-w-7xl px-6 pb-32 md:px-12">
		<div
			class="mx-auto grid max-w-4xl gap-px border border-zinc-200 bg-zinc-200 md:grid-cols-3 dark:border-zinc-900 dark:bg-zinc-800"
		>
			<div class="flex flex-col gap-3 bg-[#f5f5f0] p-8 dark:bg-zinc-900">
				<div class="dot-icon" aria-hidden="true"></div>
				<h3 class="text-xl font-bold tracking-[0.2em] text-zinc-800 uppercase dark:text-zinc-100">
					Map View
				</h3>
				<p class="text-md leading-relaxed text-zinc-900 dark:text-zinc-300">
					See how your commute would look like each day on the map view.
				</p>
			</div>
			<div class="flex flex-col gap-3 bg-[#f5f5f0] p-8 dark:bg-zinc-900">
				<div class="dot-icon" aria-hidden="true"></div>
				<h3 class="text-xl font-bold tracking-[0.2em] text-zinc-800 uppercase dark:text-zinc-100">
					Professor Ratings
				</h3>
				<p class="text-md leading-relaxed text-zinc-900 dark:text-zinc-300">
					Incorporates RateMyProfessor data so you know if a section is worth your time before you
					enrol.
				</p>
			</div>
			<div class="flex flex-col gap-3 bg-[#f5f5f0] p-8 dark:bg-zinc-900">
				<div class="dot-icon" aria-hidden="true"></div>
				<h3 class="text-xl font-bold tracking-[0.2em] text-zinc-800 uppercase dark:text-zinc-100">
					Your Life
				</h3>
				<p class="text-md leading-relaxed text-zinc-900 dark:text-zinc-300">
					Job schedule, goals, learning style are factor in the scheduling process.
				</p>
			</div>
		</div>
	</section>

	<footer
		class="w-full border-t border-zinc-300 bg-[#f5f5f0]/80 py-12 backdrop-blur-sm dark:border-zinc-900 dark:bg-zinc-950/80"
	>
		<div
			class="mx-auto flex max-w-7xl flex-col items-center justify-between gap-8 px-6 text-center md:flex-row md:px-12 md:text-left"
		>
			<div>
				<div
					class="mb-2 text-sm font-bold tracking-[0.3em] text-zinc-800 uppercase dark:text-zinc-100"
				>
					PathWeave
				</div>
				<p
					class="text-[10px] font-medium tracking-[0.2em] text-zinc-900 uppercase dark:text-zinc-300"
				>
					Your McMaster year, perfectly balanced.
				</p>
			</div>
			<div class="flex flex-col items-center gap-4 md:items-end">
				<div
					class="flex gap-6 text-[10px] font-bold tracking-[0.2em] text-zinc-900 uppercase dark:text-zinc-300"
				>
					{#if data.user?.onboarded}
						<a href={resolve('/plans')} class="link"
							>Go to Plans</a
						>
					{:else if data.user}
						<a
							href={resolve('/onboarding')}
							class="link"
							>Continue Onboarding</a
						>
					{:else}
						<a href={resolve('/login')} class="link"
							>Login</a
						>
					{/if}
				</div>
				<div class="text-[12px] tracking-[0.2em] text-zinc-800 dark:text-zinc-400">
					© 2026 PathWeave. Made by <a
						target="_blank"
						class="underline underline-offset-4 hover:font-bold hover:text-brand-purple hover:decoration-brand-purple hover:decoration-2"
						href="https://www.linkedin.com/in/toheeb-eji-880b72325/">Toheeb Eji</a
					> for students.
				</div>
			</div>
		</div>
	</footer>
</main>
