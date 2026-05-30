<script lang="ts">
	import { cn } from '$lib/utils';
	import { theme } from 'mode-watcher';
	import { PlusIcon } from 'phosphor-svelte';
	let { index } = $props();

	const tints = ['bg-purple', 'bg-blue', 'bg-teal', 'bg-rose'] as const;
	const tint = $derived(tints[index % tints.length] + theme.current == 'light' ? ' 200' : ' 800');
</script>

<div
	class={cn(
		'text-md hover:bg-bg-brand-purple/50 relative flex aspect-square size-full w-full flex-col rounded-2xl border-2 border-dashed border-primary bg-secondary/50 p-5 font-medium text-secondary-foreground drop-shadow-xs drop-shadow-[#c5aaf7] transition ease-out text-shadow-xs hover:scale-105 hover:border-none hover:ring-2 hover:ring-[#AE87F7] active:translate-y-0.75 sm:size-90 md:size-70 lg:size-90 dark:drop-shadow-[#a87ff4]',
		tint
	)}
>
	<PlusIcon size={40} />
</div>
