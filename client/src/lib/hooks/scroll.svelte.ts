class ScrollState {
	y = $state(0);
	isScrolled = $derived(this.y > 50);
}

export const scrollState = new ScrollState();
