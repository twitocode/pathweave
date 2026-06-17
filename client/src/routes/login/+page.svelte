<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
	import Google from '$lib/components/svg/google.svelte';
	import { Button } from '$lib/components/ui/button';
	import { getAuthLoginHref } from '$lib/server-url';
</script>

<svelte:head>
	<title>Sign in | PathWeave</title>
</svelte:head>

<main
	class=" relative flex min-h-screen flex-col text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />
	<div class="flex flex-1 items-center justify-center px-6">
		<div class="w-full max-w-md p-8 md:grid-cols-3">
			<h1 class="mb-3 text-3xl leading-tight font-bold tracking-tight sm:text-4xl">Sign in</h1>
			<p class="mb-10 text-[14px] leading-relaxed tracking-wide text-zinc-900 dark:text-zinc-300">
				Continue with your Google account to get started.
			</p>

			<Button
				href={getAuthLoginHref()}
				variant="secondary"
				size="sm"
				class="shadow-[inset_0_0_5px_1px_rgba(255,255,255,0.2)]"
			>
				<span class="inline-flex size-6 shrink-0 items-center justify-center">
					<Google />
				</span>
				Continue with Google
			</Button>
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
