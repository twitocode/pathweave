<script lang="ts">
	import CourseSearch from '$lib/components/plans/course-search.svelte';
	import Course from '$lib/components/plans/course.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeftIcon } from 'phosphor-svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const plan = $derived(data.plan);
</script>

<main class="mt-40 flex h-full w-full flex-col gap-4">
	<section>
		<Button variant="link" class="gap-1 p-0" href="/plans">
			<ArrowLeftIcon />
			<span>Plans</span>
		</Button>
	</section>
	<section>
		<h1 class="md:font-4xl font-gro text-3xl font-bold text-primary md:text-5xl">
			{plan?.title}
		</h1>
	</section>
	<section class="grid h-full gap-4 md:grid-cols-3">
		<section class="">
			<CourseSearch term={plan?.term} />
			<div>
				{#each plan?.courses || [] as course}
					<Course info={course} />
				{/each}
			</div>
		</section>
		<section class="col-span-2 bg-primary"></section>
	</section>
</main>
