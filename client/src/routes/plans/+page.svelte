<script lang="ts">
	import Navbar from '$lib/components/navbar.svelte';
	import AddPlan from '$lib/components/plans/add-plan.svelte';
	import PlanComp from '$lib/components/plans/plan.svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import Input from '$lib/components/ui/input/input.svelte';
	import Label from '$lib/components/ui/label/label.svelte';
	import * as Select from '$lib/components/ui/select/index.js';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let selectedTerm = $state('Fall 2027');
	$effect(() => console.log(data.plans));
</script>

<svelte:head>
	<title>Plans | PathWeave</title>
</svelte:head>

<main
	class="dotmatrix-bg flex min-h-screen flex-col text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
>
	<Navbar />

	<div class="mt-40 flex flex-1 flex-col px-6 md:px-12">
		<span>You're in</span>
		<h1 class="md:font-4xl text-3xl font-bold text-primary">{data.programName}</h1>

		<div class="my-20">
			<span class="text-xl">Plans</span>
			<div class="mt-4 grid gap-8 md:grid-cols-3">
				{#each data.plans as plan (plan.id)}
					<PlanComp {plan} />
				{/each}
				<Dialog.Root>
					<Dialog.Trigger><AddPlan /></Dialog.Trigger>
					<Dialog.Content class="sm:max-w-md">
						<Dialog.Header>
							<Dialog.Title>New Plan</Dialog.Title>
							<Dialog.Description>Choose a new name and term</Dialog.Description>
						</Dialog.Header>
						<div class="flex items-center gap-2">
							<div class="grid flex-1 gap-2">
								<Label for="Title" class="sr-only">Title</Label>
								<Input id="Title" placeholder="Ex. Commuting Plan" />
							</div>
							<div class="grid flex-1 gap-2">
								<Label for="term" class="sr-only">Term</Label>
								<Select.Root type="single" bind:value={selectedTerm}>
									<Select.Trigger
										id="term"
										class="flex h-10 w-full min-w-0 items-center justify-between"
									>
										<span class="min-w-0 flex-1 truncate text-left">{selectedTerm}</span>
									</Select.Trigger>
									<Select.Content
										class="border border-zinc-200 bg-[#f5f5f0] dark:border-zinc-800 dark:bg-zinc-900"
									>
										<Select.Item value="Fall 2026" label="Fall 2026" class="text-xs" />
										<Select.Item value="Winter 2027" label="Winter 2027" class="text-xs" />
										<Select.Item
											value="Spring/Summer 2027"
											label="Spring/Summer 2027"
											class="text-xs"
										/>
									</Select.Content>
								</Select.Root>
							</div>
						</div>
						<Dialog.Footer class="sm:justify-start">
							<Button type="submit">Create</Button>
						</Dialog.Footer>
					</Dialog.Content>
				</Dialog.Root>
			</div>
		</div>
	</div>

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
