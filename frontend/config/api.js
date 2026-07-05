// Nik_kiT — API client config.
//
// The app talks to the Django backend (the `app` container) on port 6061.
// - On a phone (Expo Go), `localhost` means the phone, so we must use the laptop's
//   LAN IP. Metro already knows it, so we reuse Metro's host automatically.
// - On web (running on the laptop), `localhost` is correct.
// - If auto-detection ever fails, we fall back to LAN_IP_FALLBACK below.

import Constants from 'expo-constants';
import { Platform } from 'react-native';

const API_PORT = 6061;
const LAN_IP_FALLBACK = '192.168.1.13'; // this laptop's current LAN IP

function resolveHost() {
  if (Platform.OS === 'web') return 'localhost';

  // Metro's host URI looks like "192.168.1.13:6060" — the part before ":" is the
  // laptop's LAN IP, exactly what the phone needs to reach the backend.
  const hostUri =
    Constants.expoConfig?.hostUri ||
    Constants.expoGoConfig?.debuggerHost ||
    '';
  const host = hostUri.split(':')[0];
  return host || LAN_IP_FALLBACK;
}

export const API_BASE_URL = `http://${resolveHost()}:${API_PORT}`;

// Tiny fetch helper so screens don't repeat the base URL / JSON parsing.
export async function apiGet(path) {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// --- Menu (M02) read helpers ---
export const getSections = () => apiGet('/api/v1/sections');
export const getRecipes = (slug) => apiGet(`/api/v1/sections/${slug}/recipes`);
export const getRecipe = (id) => apiGet(`/api/v1/recipes/${id}`);
export const getStoreStatus = () => apiGet('/api/v1/store/status');

// --- Generic request (POST/PATCH/DELETE) with token + cart-key headers ---
export async function apiRequest(method, path, { body, token, cartKey } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (cartKey) headers['X-Cart-Key'] = cartKey;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg = data?.error?.message || `HTTP ${res.status}`;
    const e = new Error(msg);
    e.status = res.status;
    e.data = data;
    throw e;
  }
  return data;
}

// --- Cart & order (M05) + auth (M01) helpers ---
export const addToCart = (item, cartKey) =>
  apiRequest('POST', '/api/v1/cart/items', { body: item, cartKey });
export const fetchCart = (cartKey) =>
  apiRequest('GET', '/api/v1/cart', { cartKey });
export const registerClient = (payload) =>
  apiRequest('POST', '/api/v1/auth/register', { body: payload });
export const placeOrder = (cartKey, token, extra = {}) =>
  apiRequest('POST', '/api/v1/orders', { body: { cart_key: cartKey, ...extra }, token, cartKey });

// --- Payment + tracking (M06/M07) ---
export const getPaymentInfo = (orderId, token) =>
  apiRequest('GET', `/api/v1/orders/${orderId}/payment`, { token });
export const getTracking = (orderId, token) =>
  apiRequest('GET', `/api/v1/orders/${orderId}/tracking`, { token });

// Multipart proof upload — let the platform set the multipart boundary itself.
export async function uploadProof(orderId, token, formData) {
  const res = await fetch(`${API_BASE_URL}/api/v1/orders/${orderId}/payment/proof`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const text = await res.text();
  if (!res.ok) throw new Error(text || `HTTP ${res.status}`);
  return text ? JSON.parse(text) : null;
}
