/**
 * Auth helpers — direct API calls, no Supabase.
 * Tokens are stored in localStorage under 'access_token' and 'refresh_token'.
 */

import api from './api';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_ID_KEY = 'user_id';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getUserId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(USER_ID_KEY);
}

function storeTokens(data: { access_token: string; refresh_token: string; user_id: string }) {
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  localStorage.setItem(USER_ID_KEY, data.user_id);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_ID_KEY);
}

export async function signUp(email: string, password: string, display_name: string) {
  const { data } = await api.post('/auth/register', { email, password, display_name });
  storeTokens(data);
  return data;
}

export async function signIn(email: string, password: string) {
  const { data } = await api.post('/auth/login', { email, password });
  storeTokens(data);
  return data;
}

export async function signOut() {
  clearTokens();
}

export async function refreshTokens() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token available.');

  const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken });
  storeTokens(data);
  return data;
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}
