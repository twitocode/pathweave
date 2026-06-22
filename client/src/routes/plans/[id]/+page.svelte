<script lang="ts">
	import CourseSearch from '$lib/components/plans/course-search.svelte';
	import Course from '$lib/components/plans/course.svelte';
	import { Button } from '$lib/components/ui/button';
	import { getPlanStore } from '$lib/stores/plan.svelte';
	import { ArrowLeftIcon } from 'phosphor-svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const store = getPlanStore();
	$effect(() => {
		store.current = data.plan;
	});
</script>

<svelte:head>
	<title>{store.current.title ?? store.current.term} | PathWeave</title>
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
			{store.current.title}
		</h1>
		<span class="">{store.termString}</span>
	</section>
	<section class="grid h-full gap-4 md:grid-cols-3">
		<section class="">
			<CourseSearch />
			<div>
				{#each store.current.courses || [] as course (course.id)}
					<Course info={course} />
				{/each}
			</div>
		</section>
		<section class="col-span-2 bg-primary"></section>
	</section>
</main>
