<script lang="ts">
	import * as Popover from '$lib/components/ui/popover/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import { cn } from '$lib/utils.js';
	import { FIELD_SHELL, LABEL_CLASS } from './constants.js';
	import { tick } from 'svelte';

	let {
		label,
		values,
		draft = $bindable(''),
		placeholder,
		chipClass,
		normalize = (s: string) => s.trim(),
		onAdd,
		onRemove,
		suggestions = []
	}: {
		label: string;
		values: readonly string[];
		draft: string;
		placeholder: string;
		chipClass: string;
		normalize?: (raw: string) => string;
		onAdd: (value: string) => void;
		onRemove: (index: number) => void;
		suggestions?: readonly { value: string; label: string }[];
	} = $props();

	let open = $state(false);
	let inputEl: HTMLInputElement | undefined = $state();

	const filteredSuggestions = $derived(
		suggestions
			.filter(
				(s) =>
					!values.includes(s.value) &&
					(s.label.toLowerCase().includes(draft.toLowerCase()) ||
						s.value.toLowerCase().includes(draft.toLowerCase()))
			)
			.slice(0, 8)
	);

	async function commit(value?: string) {
		const v = normalize(value ?? draft);
		if (!v || values.includes(v)) return;
		onAdd(v);
		draft = '';
		open = false;
		await tick();
		inputEl?.focus();
	}

	function labelForValue(value: string) {
		return suggestions.find((s) => s.value === value)?.label ?? value;
	}
</script>

<div class="space-y-2">
	<p class={LABEL_CLASS}>{label}</p>

	<Popover.Root bind:open>
		<div
			class={cn(FIELD_SHELL, 'relative flex min-h-10 flex-wrap items-center gap-1.5')}
			role="presentation"
			onclick={() => inputEl?.focus()}
		>
			{#each values as item, i (item + i)}
				<button type="button" class={cn(chipClass, 'shrink-0')} onclick={() => onRemove(i)}>
					{item}
					<span class="opacity-60">×</span>
				</button>
			{/each}

			<input
				bind:this={inputEl}
				bind:value={draft}
				onkeydown={(e) => {
					if (e.key === 'Enter') {
						e.preventDefault();
						if (filteredSuggestions.length > 0) {
							commit(filteredSuggestions[0].value);
						} else {
							commit();
						}
					}
					if (e.key === 'Backspace' && draft === '' && values.length > 0) {
						onRemove(values.length - 1);
					}
				}}
				oninput={() => {
					open = draft.length > 0 && suggestions.length > 0;
				}}
				onfocus={() => {
					if (draft.length > 0 && suggestions.length > 0) {
						open = true;
					}
				}}
				class={cn(
					'h-full min-w-24 flex-1 border-0 bg-transparent py-0 text-xs placeholder:text-zinc-400 focus:ring-0 focus:outline-none dark:placeholder:text-zinc-500',
					{
						'px-0': values.length == 0,
						'px-1': values.length > 0
					}
				)}
				{placeholder}
			/>

			<Popover.Trigger class="pointer-events-none absolute inset-0 opacity-0" aria-hidden="true" />
		</div>

		{#if filteredSuggestions.length > 0}
			<Popover.Content
				align="start"
				sideOffset={4}
				onInteractOutside={(e) => {
					if (inputEl?.contains(e.target as Node)) {
						e.preventDefault();
					}
				}}
				onOpenAutoFocus={(e) => {
					e.preventDefault();
				}}
				class="w-(--bits-popover-anchor-width) border border-zinc-200 bg-[#f5f5f0] p-0 dark:border-zinc-800 dark:bg-zinc-900"
			>
				<Command.Root shouldFilter={false}>
					<Command.List class="max-h-48 overflow-y-auto">
						<Command.Group>
							{#each filteredSuggestions as s (s.value)}
								<Command.Item value={s.label} onSelect={() => commit(s.value)} class="text-xs">
									<span class="line-clamp-2 leading-snug whitespace-normal">{s.label}</span>
								</Command.Item>
							{/each}
						</Command.Group>
					</Command.List>
				</Command.Root>
			</Popover.Content>
		{/if}
	</Popover.Root>
</div>
