// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user: {
				id: string;
				email: string;
				onboarded: boolean;
			} | null;
		}
		interface PageData {
			user: App.Locals['user'];
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
