<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
</script>

<svelte:head>
	<title>Onboarding | PathWeave</title>
</svelte:head>

<main
	class="dotmatrix-bg relative flex min-h-screen flex-col font-geist-pixel text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />
	<div class="flex flex-1 items-center justify-center px-6">Onboarding</div>
	<footer
		class="w-full border-t border-zinc-200 bg-[#f5f5f0]/80 py-6 backdrop-blur-sm dark:border-zinc-900 dark:bg-zinc-950/80"
	>
		<div class="mx-auto max-w-7xl px-6 md:px-12">
			<div class="text-[10px] tracking-[0.2em] text-zinc-600 dark:text-zinc-400">
				© 2026 PathWeave
			</div>
		</div>
	</footer>
</main>
