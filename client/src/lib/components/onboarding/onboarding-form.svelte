<script lang="ts">
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';
	import { type SuperValidated, superForm } from 'sveltekit-superforms';
	import { zod4Client } from 'sveltekit-superforms/adapters';
	import Navbar from '$lib/components/navbar.svelte';
	import OnboardingProgress from './onboarding-progress.svelte';
	import OnboardingStepHeading from './onboarding-step-heading.svelte';
	import OnboardingStepGoals from './onboarding-step-learning.svelte';
	import OnboardingStepIdentity from './onboarding-step-identity.svelte';
	import OnboardingStepLife from './onboarding-step-life.svelte';
	import OnboardingStepNav from './onboarding-step-nav.svelte';
	import {
		onboardingSchema,
		step1Schema,
		step2Schema,
		type OnboardingFormData
	} from './schema.js';

	let { data }: { data: { form: SuperValidated<OnboardingFormData> } } = $props();

	// svelte-ignore state_referenced_locally
	const form = superForm(data.form, {
		validators: zod4Client(onboardingSchema),
		validationMethod: 'onblur',
		resetForm: false,
		dataType: 'json',
	});
	const { form: formData, enhance, submitting, errors } = form;

	let step = $state(1);



	function validateStep1() {
		const d = get(formData);
		const r = step1Schema.safeParse(d);
		if (!r.success) {
			const fe = r.error.flatten().fieldErrors;
			errors.update((e) => {
				for (const [k, v] of Object.entries(fe)) {
					// @ts-ignore
					e[k] = v;
				}
				return e;
			});
			return false;
		}
		return true;
	}

	function validateStep2() {
		const d = get(formData);
		const r = step2Schema.safeParse(d);
		if (!r.success) {
			const fe = r.error.flatten().fieldErrors;
			errors.update((e) => {
				for (const [k, v] of Object.entries(fe)) {
					// @ts-ignore
					e[k] = v;
				}
				return e;
			});
			return false;
		}
		return true;
	}

	function next() {
		errors.clear();
		if (step === 1) {
			if (!validateStep1()) return;
			step = 2;
			return;
		}
		if (step === 2) {
			if (!validateStep2()) return;
			step = 3;
		}
	}

	function back() {
		errors.clear();
		if (step === 1) {
			goto('/');
			return;
		}
		step -= 1;
	}
</script>

<form method="POST" class="contents" use:enhance>
	<main
		class="dotmatrix-bg relative flex min-h-screen flex-col font-geist-pixel text-zinc-900 selection:bg-brand-purple selection:text-white dark:text-zinc-100"
	>
		<Navbar />

		<div class="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 pt-24 pb-16 md:px-12">
			<OnboardingProgress {step} />
			<OnboardingStepHeading {step} />

			<div class="mx-auto w-full max-w-2xl">
				{#if step === 1}
					<OnboardingStepIdentity {form} {formData} />
				{:else if step === 2}
					<OnboardingStepLife {form} {formData} />
				{:else}
					<OnboardingStepGoals {form} {formData} />
				{/if}
			</div>

			<div class="mx-auto w-full max-w-2xl">
				<OnboardingStepNav {step} submitting={$submitting} onBack={back} onNext={next} />
			</div>
		</div>

		<footer
			class="w-full border-t border-zinc-200 bg-[#f5f5f0]/80 py-6 backdrop-blur-sm dark:border-zinc-900 dark:bg-zinc-950/80"
		>
			<div class="mx-auto max-w-7xl px-6 md:px-12">
				<div class="text-[10px] tracking-[0.2em] text-zinc-600 dark:text-zinc-400">
					© 2026 PathWeave
				</div>
			</div>
		</footer>
	</main>
</form>
