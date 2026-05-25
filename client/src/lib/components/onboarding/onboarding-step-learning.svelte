<script lang="ts">
	import type { Writable } from 'svelte/store';
	import type { SuperForm } from 'sveltekit-superforms';
	import * as Form from '$lib/components/ui/form/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { cn } from '$lib/utils.js';
	import OnboardingChipsField from './onboarding-chips-field.svelte';
	import { LABEL_CLASS, professorBand, teachingStyleBand, COURSES } from './constants.js';
	import type { OnboardingFormData } from './schema.js';

	let {
		form,
		formData
	}: {
		form: SuperForm<OnboardingFormData>;
		formData: Writable<OnboardingFormData>;
	} = $props();

	let draftAvoided = $state('');
</script>

<div class="space-y-10">
	<div class="space-y-8">
		<Form.Field {form} name="professorQuality">
			<Form.Control>
				{#snippet children({ props })}
					<div class="space-y-3">
						<Form.Label class={LABEL_CLASS}>Professor Quality</Form.Label>
						<p class="text-xs font-bold text-zinc-700 dark:text-zinc-300">
							{professorBand($formData.professorQuality)}
						</p>
						<Slider
							type="single"
							id={props.id}
							aria-describedby={props['aria-describedby']}
							aria-invalid={props['aria-invalid']}
							data-fs-error={props['data-fs-error']}
							data-fs-control={props['data-fs-control']}
							min={1}
							max={3}
							step={1}
							value={$formData.professorQuality}
							onValueChange={(v: number) => {
								$formData.professorQuality = v;
							}}
							class="py-2"
						/>
						<div
							class="relative flex w-full text-[9px] font-bold tracking-[0.15em] text-zinc-400 uppercase dark:text-zinc-500"
						>
							<span class="w-1/3 text-left">Doesn't matter</span>
							<span class="w-1/3 text-center">Can be alright</span>
							<span class="w-1/3 text-right">Must be perfect</span>
						</div>
					</div>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>

		<Form.Field {form} name="teachingStyle">
			<Form.Control>
				{#snippet children({ props })}
					<div class="space-y-3">
						<Form.Label class={LABEL_CLASS}>Teaching Style</Form.Label>
						<p class="text-xs font-bold text-zinc-700 dark:text-zinc-300">
							{teachingStyleBand($formData.teachingStyle)}
						</p>
						<Slider
							type="single"
							id={props.id}
							aria-describedby={props['aria-describedby']}
							aria-invalid={props['aria-invalid']}
							data-fs-error={props['data-fs-error']}
							data-fs-control={props['data-fs-control']}
							min={1}
							max={3}
							step={1}
							value={$formData.teachingStyle}
							onValueChange={(v: number) => {
								$formData.teachingStyle = v;
							}}
							class="py-2"
						/>
						<div
							class="relative flex w-full text-[9px] font-bold tracking-[0.15em] text-zinc-400 uppercase dark:text-zinc-500"
						>
							<span class="w-1/3 text-left">Traditional</span>
							<span class="w-1/3 text-center">Interactive</span>
							<span class="w-1/3 text-right">Engaging</span>
						</div>
					</div>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>
	</div>

	<OnboardingChipsField
		label="Avoided Courses"
		values={$formData.avoidedCourses}
		bind:draft={draftAvoided}
		suggestions={COURSES}
		placeholder="Search for a course..."
		chipClass="inline-flex items-center gap-1 border border-brand-red/30 bg-brand-red/10 px-2 py-0.5 text-[10px] font-bold tracking-[0.1em] uppercase text-brand-red dark:border-brand-red/40 dark:bg-brand-red/15"
		normalize={(s) => s.trim().toUpperCase()}
		onAdd={(v) => {
			$formData.avoidedCourses = [...$formData.avoidedCourses, v];
		}}
		onRemove={(i) => {
			$formData.avoidedCourses = $formData.avoidedCourses.filter((_, idx) => idx !== i);
		}}
	/>
</div>
