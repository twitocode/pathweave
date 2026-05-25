<script lang="ts">
	import { Command as CommandPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import MagnifyingGlassIcon from 'phosphor-svelte/lib/MagnifyingGlass';

	let {
		ref = $bindable(null),
		class: className,
		value = $bindable(''),
		...restProps
	}: CommandPrimitive.InputProps = $props();
</script>

<div data-slot="command-input-wrapper" class="border-b pb-0">
	<div
		class="relative flex h-8 w-full min-w-0 items-center border-none border-input/30 bg-input/30 shadow-none"
	>
		<CommandPrimitive.Input
			{value}
			data-slot="command-input"
			class={cn(
				'w-full text-xs outline-hidden disabled:cursor-not-allowed disabled:opacity-50',
				className
			)}
			{...restProps}
		>
			{#snippet child({ props })}
				<Input
					{...props}
					bind:value
					bind:ref
					class="flex-1 rounded-none border-0 bg-transparent shadow-none ring-0 focus-visible:ring-0"
				/>
			{/snippet}
		</CommandPrimitive.Input>
		<div class="flex shrink-0 items-center justify-center pl-2 text-muted-foreground">
			<MagnifyingGlassIcon class="size-4 shrink-0 opacity-50" />
		</div>
	</div>
</div>
