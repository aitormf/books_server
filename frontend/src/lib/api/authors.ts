import { env } from '$env/dynamic/public';
import type { Author, AuthorFormData } from './types';

const BASE = () => env.PUBLIC_AUTHORS_API;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE()}${path}`, {
		...init,
		headers: { 'Content-Type': 'application/json', ...init?.headers }
	});
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new Error(body?.detail ?? `Request failed: ${res.status}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json();
}

export function listAuthors(): Promise<Author[]> {
	return request('/authors');
}

export function getAuthor(id: number): Promise<Author> {
	return request(`/authors/${id}`);
}

export function createAuthor(data: AuthorFormData): Promise<Author> {
	return request('/authors', { method: 'POST', body: JSON.stringify(data) });
}

export function updateAuthor(id: number, data: AuthorFormData): Promise<Author> {
	return request(`/authors/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

export function deleteAuthor(id: number): Promise<void> {
	return request(`/authors/${id}`, { method: 'DELETE' });
}
