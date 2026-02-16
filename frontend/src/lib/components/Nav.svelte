<script lang="ts">
	import { page } from '$app/state';
</script>

<nav class="bg-gray-800 text-white px-6 py-3 flex items-center gap-6">
	<span class="font-bold text-lg">Library</span>
	<a
		href="/authors"
		class="px-3 py-1 rounded transition-colors {page.url.pathname.startsWith('/authors')
			? 'bg-gray-600'
			: 'hover:bg-gray-700'}"
	>
		Authors
	</a>
	<a
		href="/books"
		class="px-3 py-1 rounded transition-colors {page.url.pathname.startsWith('/books')
			? 'bg-gray-600'
			: 'hover:bg-gray-700'}"
	>
		Books
	</a>
</nav>
