<script lang="ts">
	import * as Form from '$lib/components/ui/form/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { cn } from '$lib/utils.js';
	import type { Writable } from 'svelte/store';
	import type { SuperForm } from 'sveltekit-superforms';
	import { FIELD_SHELL, LABEL_CLASS, TIME_OPTIONS, labelForTime } from './constants.js';
	import OnboardingMapPanel from './onboarding-map-panel.svelte';
	import type { OnboardingFormData } from './schema.js';

	let {
		form,
		formData
	}: {
		form: SuperForm<OnboardingFormData>;
		formData: Writable<OnboardingFormData>;
	} = $props();
</script>

<div class="flex flex-col items-center">
	<div class="w-full max-w-[400px] shrink-0 space-y-10 lg:space-y-8">
		<div class="grid gap-6 md:grid-cols-2">
			<Form.Field {form} name="wakeUpTime">
				<Form.Control>
					{#snippet children({ props })}
						<Form.Label class={LABEL_CLASS}
							>Wake-Up Time <span class="translate-y-[4px] text-xl font-bold text-brand-red">*</span
							></Form.Label
						>
						<Select.Root type="single" bind:value={$formData.wakeUpTime}>
							<Select.Trigger
								{...props}
								class={cn(
									FIELD_SHELL,
									'mt-2 flex h-10 w-full min-w-0 items-center justify-between'
								)}
							>
								<span class="truncate text-left">
									{labelForTime($formData.wakeUpTime)}
								</span>
							</Select.Trigger>
							<Select.Content
								class="max-h-64 overflow-y-auto border border-zinc-200 bg-[#f5f5f0] dark:border-zinc-800 dark:bg-zinc-900"
							>
								{#each TIME_OPTIONS as t (t.value)}
									<Select.Item value={t.value} label={t.label} class="text-xs" />
								{/each}
							</Select.Content>
						</Select.Root>
					{/snippet}
				</Form.Control>
				<Form.FieldErrors />
			</Form.Field>

			<Form.Field {form} name="bedtime">
				<Form.Control>
					{#snippet children({ props })}
						<Form.Label class={LABEL_CLASS}
							>Bedtime <span class="translate-y-[4px] text-xl font-bold text-brand-red">*</span
							></Form.Label
						>
						<Select.Root type="single" bind:value={$formData.bedtime}>
							<Select.Trigger
								{...props}
								class={cn(
									FIELD_SHELL,
									'mt-2 flex h-10 w-full min-w-0 items-center justify-between'
								)}
							>
								<span class="truncate text-left">
									{labelForTime($formData.bedtime)}
								</span>
							</Select.Trigger>
							<Select.Content
								class="max-h-64 overflow-y-auto border border-zinc-200 bg-[#f5f5f0] dark:border-zinc-800 dark:bg-zinc-900"
							>
								{#each TIME_OPTIONS as t (t.value)}
									<Select.Item value={t.value} label={t.label} class="text-xs" />
								{/each}
							</Select.Content>
						</Select.Root>
					{/snippet}
				</Form.Control>
				<Form.FieldErrors />
			</Form.Field>
		</div>

		<Form.Field {form} name="onCampus">
			<Form.Control>
				{#snippet children({ props })}
					<div
						class="flex items-center justify-between gap-4 border border-zinc-200 bg-[#f5f5f0] px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900"
					>
						<div class="space-y-0.5">
							<Form.Label class="text-xs font-bold text-zinc-900 dark:text-zinc-100"
								>Will you be on campus?</Form.Label
							>
						</div>
						<Switch {...props} bind:checked={$formData.onCampus} />
					</div>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>

		<OnboardingMapPanel
			visible={!$formData.onCampus}
			bind:lat={$formData.lat}
			bind:lng={$formData.lng}
		/>

		<Form.Field {form} name="jobInfo">
			<Form.Control>
				{#snippet children({ props })}
					<Form.Label class={LABEL_CLASS}>Job Info</Form.Label>
					<Textarea
						{...props}
						bind:value={$formData.jobInfo}
						placeholder="If you have one, type in your schedule for your job."
						class={cn(FIELD_SHELL, 'mt-2 min-h-24 resize-none')}
					/>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>

		<Form.Field {form} name="futurePlans">
			<Form.Control>
				{#snippet children({ props })}
					<Form.Label class={LABEL_CLASS}>Future Plans</Form.Label>
					<Textarea
						{...props}
						bind:value={$formData.futurePlans}
						placeholder="If you know what you want to do after your degree, type it here."
						class={cn(FIELD_SHELL, 'mt-2 min-h-24 resize-none')}
					/>
				{/snippet}
			</Form.Control>
			<Form.FieldErrors />
		</Form.Field>
	</div>
</div>
