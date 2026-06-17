<script lang="ts">
	import CourseSearch from '$lib/components/plans/course-search.svelte';
	import Course from '$lib/components/plans/course.svelte';
	import { Button } from '$lib/components/ui/button';
	import { getTermString } from '$lib/utils';
	import { ArrowLeftIcon } from 'phosphor-svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const plan = $derived(data.plan);
</script>

<svelte:head>
	<title>{plan?.title ?? plan?.term} | PathWeave</title>
</svelte:head>

<main class="mt-40 flex h-full w-full flex-col gap-4">
	<section>
		<Button variant="link" class="gap-1 p-0" href="/plans">
			<ArrowLeftIcon />
			<span>Plans</span>
		</Button>
	</section>
	<section class="space-y-2">
		<h1 class="md:font-4xl font-gro text-3xl font-bold text-primary md:text-5xl">
			{plan?.title}
		</h1>
		<span class="">{getTermString(plan!.term)}</span>
	</section>
	<section class="grid h-full gap-4 md:grid-cols-3">
		<section class="">
			<CourseSearch term={plan?.term} />
			<div>
				{#each plan?.courses || [] as course (course.id)}
					<Course info={course} />
				{/each}
			</div>
		</section>
		<section class="col-span-2 bg-primary"></section>
	</section>
</main>
