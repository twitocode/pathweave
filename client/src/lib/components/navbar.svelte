<script lang="ts">
	import { page } from '$app/state';
	import { mode, toggleMode } from 'mode-watcher';
	import { Moon, SignOut, Sun } from 'phosphor-svelte';

	let { isScrolled = false } = $props();

  console.log(page.data.user)
	const loggedIn = $derived(page.data.user != null);
	const path = $derived(page.data.path ?? page.url.pathname);
</script>

<nav
	class="fixed top-0 z-50 w-full transition-all duration-300 {isScrolled
		? 'bg-[#f5f5f0]/90 backdrop-blur-sm dark:bg-zinc-950/90'
		: 'bg-transparent'}"
>
	<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 md:px-12">
		<a
			href="/"
			class="font-geist-pixel text-sm font-bold tracking-[0.3em] uppercase transition-colors hover:text-zinc-600 dark:text-zinc-100 dark:hover:text-zinc-400"
		>
			PathWeave
		</a>
		<div class="flex items-center gap-3">
			{#if page.url.pathname !== '/login' && !path.includes('plans')}
				{#if loggedIn}
					<a
						href="/plans"
						class="text-xs font-bold tracking-[0.2em] text-zinc-500 uppercase transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
					>
						Plans
					</a>
				{:else}
					<a
						href="/login"
						class="text-xs font-bold tracking-[0.2em] text-zinc-500 uppercase transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
					>
						Login
					</a>
				{/if}
			{/if}
			{#if loggedIn}
				<form method="POST" action="/logout">
					<button
						type="submit"
						class="inline-flex h-9 w-9 items-center justify-center border border-zinc-300 bg-[#f5f5f0]/90 text-zinc-900 transition-colors hover:border-zinc-500 hover:text-zinc-900 dark:border-zinc-900 dark:bg-zinc-900/80 dark:text-zinc-200 dark:hover:border-zinc-400"
						aria-label="Log out"
						title="Log out"
					>
						<SignOut class="h-3.5 w-3.5" weight="bold" />
					</button>
				</form>
			{/if}
			<button
				type="button"
				class="inline-flex h-9 w-9 items-center justify-center border border-zinc-300 bg-[#f5f5f0]/90 text-zinc-900 transition-colors hover:border-zinc-500 hover:text-zinc-900 dark:border-zinc-900 dark:bg-zinc-900/80 dark:text-zinc-200 dark:hover:border-zinc-400"
				aria-label="Toggle light and dark mode"
				aria-pressed={mode.current === 'dark'}
				onclick={toggleMode}
			>
				{#if mode.current === 'dark'}
					<Sun class="h-3.5 w-3.5" weight="bold" />
				{:else}
					<Moon class="h-3.5 w-3.5" weight="bold" />
				{/if}
			</button>
		</div>
	</div>
</nav>
