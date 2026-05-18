<script lang="ts">
	import { OnboardingForm } from '$lib/components/onboarding/index.js';
	import type { PageData } from './$types.js';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Onboarding | PathWeave</title>
</svelte:head>

<OnboardingForm {data} />
