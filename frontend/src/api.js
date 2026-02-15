const BASE = '';  // Vite proxy handles routing

export default async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  const opts = { credentials: 'include', ...options };
  if (options && options.headers) opts.headers = options.headers;
  return fetch(url, opts);
}