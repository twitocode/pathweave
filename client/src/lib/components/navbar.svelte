<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button';
	import { mode, toggleMode } from 'mode-watcher';
	import { MoonIcon, SignOutIcon, SunIcon } from 'phosphor-svelte';

	let { isScrolled = false } = $props();

	console.log(page.data.user);
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
			class="text-sm font-bold tracking-[0.3em] uppercase transition-colors hover:text-zinc-600 dark:text-zinc-100 dark:hover:text-zinc-400"
		>
			PathWeave
		</a>
		<div class="flex items-center gap-3">
			{#if page.url.pathname !== '/login' && !path.includes('plans')}
				{#if loggedIn}
					<a href="/plans" class="link"> Plans </a>
				{:else}
					<a href="/login" class="link"> Login </a>
				{/if}
			{/if}
			{#if loggedIn}
				<form method="POST" action="/logout" class="leading-none">
					<Button type="submit" variant="ghost" size="icon" aria-label="Log out" title="Log out">
						<SignOutIcon weight="bold" />
					</Button>
				</form>
			{/if}
			<Button
				variant="ghost"
				size="icon"
				aria-label="Toggle light and dark mode"
				aria-pressed={mode.current === 'dark'}
				onclick={toggleMode}
			>
				{#if mode.current === 'dark'}
					<SunIcon weight="bold" />
				{:else}
					<MoonIcon weight="bold" />
				{/if}
			</Button>
		</div>
	</div>
</nav>
