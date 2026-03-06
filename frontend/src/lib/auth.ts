const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user_id: string;
}

export function getStoredTokens(): AuthTokens | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('auth_tokens');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeTokens(tokens: AuthTokens): void {
  localStorage.setItem('auth_tokens', JSON.stringify(tokens));
}

export function clearTokens(): void {
  localStorage.removeItem('auth_tokens');
}

export async function signUp(
  email: string,
  password: string,
  display_name: string,
): Promise<AuthTokens> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, display_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registratie mislukt.');
  }
  const tokens: AuthTokens = await res.json();
  storeTokens(tokens);
  return tokens;
}

export async function signIn(email: string, password: string): Promise<AuthTokens> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Inloggen mislukt.');
  }
  const tokens: AuthTokens = await res.json();
  storeTokens(tokens);
  return tokens;
}

export async function refreshTokens(): Promise<AuthTokens | null> {
  const current = getStoredTokens();
  if (!current?.refresh_token) return null;
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: current.refresh_token }),
  });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  const tokens: AuthTokens = await res.json();
  storeTokens(tokens);
  return tokens;
}

export function signOut(): void {
  clearTokens();
  window.location.href = '/auth/login';
}

export function getAccessToken(): string | null {
  return getStoredTokens()?.access_token ?? null;
}
