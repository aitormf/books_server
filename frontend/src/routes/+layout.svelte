<script lang="ts">
	import '../app.css';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<title>Library</title>
</svelte:head>

<div class="min-h-screen bg-gray-100">
	<Nav />
	<main class="max-w-5xl mx-auto p-6">
		{@render children()}
	</main>
</div>
