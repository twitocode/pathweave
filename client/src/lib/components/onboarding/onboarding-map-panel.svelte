<script lang="ts">
	import { PUBLIC_MAPBOX_ACCESS_TOKEN } from '$env/static/public';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { cn } from '$lib/utils.js';
	import mapboxgl from 'mapbox-gl';
	import 'mapbox-gl/dist/mapbox-gl.css';
	import { InfoIcon, MapPinArea } from 'phosphor-svelte';
	import CheckIcon from 'phosphor-svelte/lib/Check';
	import { FIELD_SHELL } from './constants.js';

	const { Map } = mapboxgl;

	let {
		visible,
		lat = $bindable(43.26139744980209),
		lng = $bindable(-79.91978613336153)
	}: { visible: boolean; lat: number; lng: number } = $props();

	let open = $state(false);
	let map: mapboxgl.Map | undefined;
	let mapContainer: HTMLElement | undefined = $state();

	let confirmedLng: number | null = $state(null);
	let confirmedLat: number | null = $state(null);
	let hasConfirmed = $derived(confirmedLng !== null && confirmedLat !== null);

	// McMaster coordinates for initial map load
	let currentLng = $state(lng);
	let currentLat = $state(lat);
	let zoom = $state(12);

	// svelte-ignore state_referenced_locally
	const initialState = { lng: currentLng, lat: currentLat, zoom };

	function updateData() {
		if (!map) return;
		zoom = map.getZoom();
		currentLng = map.getCenter().lng;
		currentLat = map.getCenter().lat;
	}

	// Initialize map when container mounts (dialog opens)
	$effect(() => {
		if (!mapContainer) return;

		const startLng = confirmedLng ?? initialState.lng;
		const startLat = confirmedLat ?? initialState.lat;

		const instance = new Map({
			container: mapContainer,
			accessToken: PUBLIC_MAPBOX_ACCESS_TOKEN,
			center: [startLng, startLat],
			zoom: initialState.zoom,
			style: 'mapbox://styles/mapbox/standard-satellite'
		});

		instance.on('move', () => {
			updateData();
		});

		map = instance;

		return () => {
			instance.remove();
			map = undefined;
		};
	});

	function handleConfirm() {
		confirmedLng = currentLng;
		confirmedLat = currentLat;
		lng = currentLng;
		lat = currentLat;
		open = false;
	}

	function handleReset() {
		if (!map) return;
		map.flyTo({
			center: [initialState.lng, initialState.lat],
			zoom: initialState.zoom,
			essential: true
		});
	}
</script>

{#if visible}
	<div class="w-full space-y-2">
		<div class="flex items-center justify-between">
			<p class="text-[10px] font-bold tracking-[0.2em] text-zinc-600 uppercase dark:text-zinc-400">
				Your Location
			</p>
			<Tooltip.Provider>
				<Tooltip.Root>
					<Tooltip.Trigger><InfoIcon /></Tooltip.Trigger>
					<Tooltip.Content>
						<p>
							Your exact location is not needed, its just so that you can see roughly how commuting
							distances affect you.
						</p>
					</Tooltip.Content>
				</Tooltip.Root>
			</Tooltip.Provider>
		</div>
		<p class="text-[11px] text-zinc-900 dark:text-zinc-300">Used for calculating distances.</p>

		<!-- Trigger Card -->
		<button
			type="button"
			onclick={() => (open = true)}
			class={cn(
				FIELD_SHELL,
				'group mt-2 flex w-full cursor-pointer items-center gap-3 px-4 py-3.5 text-left transition-all hover:border-zinc-400 dark:hover:border-zinc-600'
			)}
		>
			<div
				class={cn(
					'flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors',
					hasConfirmed
						? 'bg-brand-purple/15 text-brand-purple'
						: 'bg-zinc-200 text-zinc-500 group-hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-400 dark:group-hover:bg-zinc-700'
				)}
			>
				{#if hasConfirmed}
					<CheckIcon size={18} weight="bold" />
				{:else}
					<MapPinArea size={18} weight="bold" />
				{/if}
			</div>
			<div class="min-w-0 flex-1">
				{#if hasConfirmed}
					<p class="truncate text-xs font-medium text-zinc-900 dark:text-zinc-100">Location set</p>
					<p class="mt-0.5 truncate text-[10px] text-zinc-500 tabular-nums dark:text-zinc-400">
						{confirmedLat?.toFixed(4)}°N, {confirmedLng?.toFixed(4)}°W
					</p>
				{:else}
					<p class="text-[13px] font-medium text-zinc-900 dark:text-zinc-100">Set your location</p>
					<p class="mt-0.5 text-[12px] text-zinc-500 dark:text-zinc-400">
						Click to choose roughly where you live
					</p>
				{/if}
			</div>
			<svg
				class="h-4 w-4 shrink-0 text-zinc-400 transition-transform group-hover:translate-x-0.5 dark:text-zinc-500"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
			</svg>
		</button>
	</div>

	<!-- Map Dialog -->
	<Dialog.Root bind:open>
		<Dialog.Content
			class="w-[calc(100%-2rem)] max-w-lg gap-0 overflow-hidden p-0 sm:max-w-lg"
			showCloseButton={false}
		>
			<div
				class="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-800"
			>
				<div>
					<h3 class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
						Rough estimate of where you live
					</h3>
					<p class="mt-0.5 text-[10px] text-zinc-500 dark:text-zinc-400">
						Pan & zoom the map, the center is your location.
					</p>
				</div>
				<button
					type="button"
					onclick={handleReset}
					class="rounded-md px-2 py-1 text-[10px] font-medium text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
				>
					Reset
				</button>
			</div>

			<!-- Map Container -->
			<div class="relative aspect-square w-full bg-zinc-900">
				<div class="map" bind:this={mapContainer}></div>

				<!-- Crosshair Overlay -->
				<div
					class="pointer-events-none absolute inset-0 flex items-center justify-center"
					aria-hidden="true"
				>
					<div class="h-24 w-24 rounded-full bg-brand-purple/20 ring-[3px] ring-brand-purple/30">
						<div class="flex h-full w-full items-center justify-center">
							<div
								class="h-2 w-2 rounded-full bg-brand-purple shadow-[0_0_8px_rgba(var(--brand-purple-rgb,139,92,246),0.6)]"
							></div>
						</div>
					</div>
				</div>

				<!-- Coordinates Badge -->
				<div
					class="absolute top-3 left-3 rounded-md bg-black/70 px-2.5 py-1.5 font-mono text-[10px] text-white/80 backdrop-blur-sm"
				>
					{currentLat.toFixed(4)}°N, {currentLng.toFixed(4)}°W
				</div>
			</div>

			<!-- Footer -->
			<div
				class="flex items-center justify-end border-t border-zinc-200 px-4 py-3 dark:border-zinc-800"
			>
				<button
					type="button"
					onclick={() => (open = false)}
					class="mr-2 rounded-md px-3 py-1.5 text-[10px] font-medium text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
				>
					Cancel
				</button>
				<button
					type="button"
					onclick={handleConfirm}
					class="rounded-md bg-brand-purple px-4 py-1.5 text-[10px] font-bold tracking-wider text-white transition-colors hover:bg-brand-purple/90"
				>
					Confirm Location
				</button>
			</div>
		</Dialog.Content>
	</Dialog.Root>
{/if}

<style>
	.map {
		position: absolute;
		width: 100%;
		height: 100%;
	}
</style>
