const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ApiError carries the HTTP status so callers can branch on 404 vs 5xx.
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
    this.name   = 'ApiError';
  }
}

async function req(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(`${BASE}${path}`, opts);
  } catch {
    // fetch() itself threw — backend is unreachable (down, CORS, network)
    throw new ApiError('Cannot reach the server. Is the backend running?', 0);
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(err.detail || res.statusText, res.status);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  createSession: (payload) => req('POST', '/game/session', payload),
  submitKick:    (id, payload) => req('POST', `/game/session/${id}/kick`, payload),
  getSession:    (id) => req('GET', `/game/session/${id}`),
  deleteSession: (id) => req('DELETE', `/game/session/${id}`),
};
