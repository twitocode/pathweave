<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import type { PlanCourse } from '$lib/types';

	interface Props {
		info: PlanCourse;
	}

	let { info }: Props = $props();

	const classTypes = $derived(
		info.types
			.map((x, i) => {
				const length = info.types.length;

				let out = length == 1 ? 'only ' : i == length - 1 ? 'and ' : '';

				if (x == 'TUT') {
					out += 'tutorials';
				} else if (x == 'SEM') {
					out += 'seminars';
				} else if (x == 'LEC') {
					out += 'lectures';
				}

				return out;
			})
			.join(', ')
	);
</script>

<div class="flex flex-col rounded-lg bg-primary p-4 text-primary-foreground">
	<span class="text-xl">
		<span class="font-bold">{info.code} </span> - <span class="truncate">{info.name}</span>
	</span>
	<span>
		Professors Include:
		<span class="space-y-2 space-x-2 font-medium">
			{#each info.teachers as teacher (teacher.id)}
				{#if teacher.name !== 'Staff'}
					<Button variant="link" class="p-0 text-white dark:text-black">{teacher.name}</Button>
				{/if}
			{/each}
		</span>
	</span>
	<span>Contains {classTypes}</span>
</div>
