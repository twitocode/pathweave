<script lang="ts" module>
	import { resolve } from '$app/paths';
	import { cn, type WithElementRef } from '$lib/utils.js';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';
	import { tv, type VariantProps } from 'tailwind-variants';

	export const buttonVariants = tv({
		base: 'inline-flex items-center justify-center bg-brand-purple text-white rounded-2xl font-medium text-md drop-shadow-sm drop-shadow-[#c5aaf7] dark:drop-shadow-[#a87ff4] hover:bg-brand-purple/80 active:translate-y-[3px] text-shadow-xs hover:ring-2 hover:ring-[#AE87F7] ease-out transition shadow-[inset_0_0_10px_1px_#7233F3]',
		variants: {
			variant: {
				default: '',
				outline:
					'text-primary bg-transparent shadow-none  hover:bg-transparent hover:text-[#AE87F7] ring-2 hover:ring-[#AE87F7]',
				secondary:
					'bg-secondary text-black/90 dark:text-white hover:bg-secondary/80 hover:ring-white/50 shadow-[inset_0_0_10px_1px_rgba(255,255,255,0.2)] drop-shadow-none',
				ghost: 'text-primary bg-transparent shadow-none  hover:bg-transparent hover:text-[#AE87F7]',
				destructive: '',
				link: 'bg-transparent text-primary dark:text-white shadow-none drop-shadow-none hover:underline hover:bg-transparent hover:ring-0 active:translate-y-0 px-0 underline-offset-8'
			},
			size: {
				default:
					"h-14 gap-4 px-6 text-2xl has-data-[icon=inline-end]:pr-6 has-data-[icon=inline-start]:pl-6 [&_svg:not([class*='size-'])]:size-7",
				xs: "h-8 gap-1.5 px-3 text-xs has-data-[icon=inline-end]:pr-2.5 has-data-[icon=inline-start]:pl-2.5 [&_svg:not([class*='size-'])]:size-3",
				sm: "h-10 gap-2 px-4 text-sm has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3 [&_svg:not([class*='size-'])]:size-4",
				lg: 'h-16 gap-4 px-10 text-3xl has-data-[icon=inline-end]:pr-8 has-data-[icon=inline-start]:pl-8 [&_svg:not([class*="size-"])]:size-8',
				icon: 'size-10 shrink-0 p-0 [&_svg]:block [&_svg]:size-4 [&_svg]:shrink-0',
				'icon-xs': 'size-8 shrink-0 p-0 [&_svg]:block [&_svg]:size-3 [&_svg]:shrink-0',
				'icon-sm': 'size-9 shrink-0 p-0 [&_svg]:block [&_svg]:size-3.5 [&_svg]:shrink-0',
				'icon-lg': 'size-12 shrink-0 p-0 [&_svg]:block [&_svg]:size-5 [&_svg]:shrink-0'
			}
		},
		defaultVariants: {
			variant: 'default',
			size: 'default'
		}
	});

	export type ButtonVariant = VariantProps<typeof buttonVariants>['variant'];
	export type ButtonSize = VariantProps<typeof buttonVariants>['size'];

	export type ButtonProps = WithElementRef<HTMLButtonAttributes> &
		WithElementRef<HTMLAnchorAttributes> & {
			variant?: ButtonVariant;
			size?: ButtonSize;
		};
</script>

<script lang="ts">
	let {
		class: className,
		variant = 'default',
		size = 'default',
		ref = $bindable(null),
		href = undefined,
		type = 'button',
		disabled,
		children,
		...restProps
	}: ButtonProps = $props();
</script>

{#if href}
	{#if href.startsWith('/')}
		<a
			bind:this={ref}
			data-slot="button"
			class={cn(buttonVariants({ variant, size }), className)}
			href={disabled ? undefined : resolve(href)}
			aria-disabled={disabled}
			role={disabled ? 'link' : undefined}
			tabindex={disabled ? -1 : undefined}
			{...restProps}
		>
			{@render children?.()}
		</a>
	{:else}
		<a
			bind:this={ref}
			data-slot="button"
			class={cn(buttonVariants({ variant, size }), className)}
			href={disabled ? undefined : href}
			aria-disabled={disabled}
			role={disabled ? 'link' : undefined}
			tabindex={disabled ? -1 : undefined}
			{...restProps}
		>
			{@render children?.()}
		</a>
	{/if}
{:else}
	<button
		bind:this={ref}
		data-slot="button"
		class={cn(buttonVariants({ variant, size }), className)}
		{type}
		{disabled}
		{...restProps}
	>
		{@render children?.()}
	</button>
{/if}
