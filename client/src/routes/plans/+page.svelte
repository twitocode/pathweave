<script lang="ts">
	import AddPlan from '$lib/components/plans/add-plan.svelte';
	import PlanComp from '$lib/components/plans/plan.svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import Input from '$lib/components/ui/input/input.svelte';
	import Label from '$lib/components/ui/label/label.svelte';
	import * as Select from '$lib/components/ui/select/index.js';
	import { PlusIcon } from 'phosphor-svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
let selectedTerm = $state('Fall 2026');
let title = $state('');
</script>

<svelte:head>
	<title>Plans | PathWeave</title>
</svelte:head>

<div class="mt-40 flex flex-1 flex-col px-6 md:px-12">
	<span class="text-xl">You're in</span>
	<h1 class="md:font-4xl font-gro text-3xl font-bold text-primary md:text-5xl">
		{data.programName}
	</h1>

	<div class="my-20 space-y-8">
		<span class="text-4xl font-bold">Plans</span>
		<div class="mt-7 grid gap-8 sm:grid-cols-2 md:grid-cols-3">
			{#each data.plans as plan, i (plan.id)}
				<PlanComp {plan} index={i} />
			{/each}
			<Dialog.Root>
				<Dialog.Trigger><AddPlan index={data.plans?.length} /></Dialog.Trigger>
				<Dialog.Content class="sm:max-w-md">
					<Dialog.Header>
						<Dialog.Title>New Plan</Dialog.Title>
						<Dialog.Description>Choose a new name and term</Dialog.Description>
					</Dialog.Header>
					<form method="POST" action="?/createPlan" class="gap-4">
						<div class="flex items-center gap-2 mb-4">
							<div class="grid flex-1 gap-2">
								<Label for="Title" class="sr-only">Title</Label>
								<Input
									id="Title"
									name="title"
									placeholder="Ex. Commuting Plan"
									bind:value={title}
								/>
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
								<input type="hidden" name="term" value={selectedTerm} />
							</div>
						</div>
						<Dialog.Footer class="sm:justify-start">
							<Button type="submit" size="sm"><PlusIcon /> Create</Button>
						</Dialog.Footer>
					</form>
				</Dialog.Content>
			</Dialog.Root>
		</div>
	</div>
</div>
