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
