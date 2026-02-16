<script lang="ts">
	import { listAuthors, createAuthor, updateAuthor, deleteAuthor } from '$lib/api/authors';
	import type { Author, AuthorFormData } from '$lib/api/types';
	import AuthorForm from '$lib/components/AuthorForm.svelte';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';

	let authors = $state<Author[]>([]);
	let loading = $state(true);
	let error = $state('');
	let showForm = $state(false);
	let editingId = $state<number | null>(null);
	let deleteTarget = $state<Author | null>(null);

	let editingAuthor = $derived(editingId ? authors.find((a) => a.id === editingId) : undefined);

	async function load() {
		loading = true;
		error = '';
		try {
			authors = await listAuthors();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load authors';
		} finally {
			loading = false;
		}
	}

	async function handleSave(data: AuthorFormData) {
		try {
			if (editingId) {
				await updateAuthor(editingId, data);
			} else {
				await createAuthor(data);
			}
			showForm = false;
			editingId = null;
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save author';
		}
	}

	async function handleDelete() {
		if (!deleteTarget) return;
		try {
			await deleteAuthor(deleteTarget.id);
			deleteTarget = null;
			await load();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete author';
		}
	}

	function startEdit(author: Author) {
		editingId = author.id;
		showForm = true;
	}

	function startCreate() {
		editingId = null;
		showForm = true;
	}

	function cancelForm() {
		showForm = false;
		editingId = null;
	}

	$effect(() => {
		load();
	});
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-gray-800">Authors</h1>
		{#if !showForm}
			<button
				class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
				onclick={startCreate}
			>
				+ New Author
			</button>
		{/if}
	</div>

	{#if error}
		<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
			{error}
			<button class="ml-2 underline" onclick={() => (error = '')}>dismiss</button>
		</div>
	{/if}

	{#if showForm}
		<AuthorForm author={editingAuthor} onsave={handleSave} oncancel={cancelForm} />
	{/if}

	{#if loading}
		<p class="text-gray-500">Loading...</p>
	{:else if authors.length === 0}
		<p class="text-gray-500">No authors found.</p>
	{:else}
		<div class="overflow-x-auto bg-white rounded-lg shadow">
			<table class="w-full text-sm text-left">
				<thead class="bg-gray-50 text-gray-600 uppercase text-xs">
					<tr>
						<th class="px-4 py-3">Name</th>
						<th class="px-4 py-3">Birth Date</th>
						<th class="px-4 py-3">Nationality</th>
						<th class="px-4 py-3">Books</th>
						<th class="px-4 py-3 text-right">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#each authors as author (author.id)}
						<tr class="hover:bg-gray-50">
							<td class="px-4 py-3 font-medium text-gray-900">{author.name}</td>
							<td class="px-4 py-3 text-gray-600">{author.birth_date ?? '-'}</td>
							<td class="px-4 py-3 text-gray-600">{author.nationality ?? '-'}</td>
							<td class="px-4 py-3 text-gray-600">{author.books.length}</td>
							<td class="px-4 py-3 text-right space-x-2">
								<button
									class="text-blue-600 hover:underline text-sm"
									onclick={() => startEdit(author)}
								>
									Edit
								</button>
								<button
									class="text-red-600 hover:underline text-sm"
									onclick={() => (deleteTarget = author)}
								>
									Delete
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<ConfirmDialog
	open={deleteTarget !== null}
	message="Are you sure you want to delete author '{deleteTarget?.name}'?"
	onconfirm={handleDelete}
	oncancel={() => (deleteTarget = null)}
/>
