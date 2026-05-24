<script lang="ts">
	import { getAuthLoginHref } from '$lib/server-url';
	import Google from '$lib/components/svg/google.svelte';
	import Navbar from '$lib/components/navbar.svelte';
</script>

<svelte:head>
	<title>Sign in | PathWeave</title>
</svelte:head>

<main
	class="dotmatrix-bg relative flex min-h-screen flex-col text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />
	<div class="flex flex-1 items-center justify-center px-6">
		<div class="w-full max-w-sm">
			<h1 class="mb-3 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
				Sign in
			</h1>
			<p class="mb-10 text-[14px] leading-relaxed tracking-wide text-zinc-900 dark:text-zinc-300">
				Continue with your Google account to get started.
			</p>

			<a
				href={getAuthLoginHref()}
				class="inline-flex w-full items-center justify-center gap-3 rounded-none border-2 border-zinc-900 bg-zinc-900 px-6 py-3.5 text-xs font-bold tracking-[0.15em] uppercase text-white transition-all hover:bg-zinc-800"
			>
				<span class="inline-flex h-4 w-4 shrink-0 items-center justify-center">
					<Google />
				</span>
				Continue with Google
			</a>
      
		</div>
	</div>

	<!-- Footer -->
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

