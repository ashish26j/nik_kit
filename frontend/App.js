// Nik_kiT — P0 boot screen.
// Its only job: prove the app can reach the backend. It pings GET /api/v1/health
// and shows the result. Real screens (menu, cart, …) arrive in P1+.

import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

import { API_BASE_URL, apiGet } from './config/api';

export default function App() {
  const [state, setState] = useState('loading'); // loading | ok | degraded | error
  const [detail, setDetail] = useState(null);

  const check = useCallback(async () => {
    setState('loading');
    setDetail(null);
    try {
      const data = await apiGet('/api/v1/health');
      setDetail(data);
      setState(data.status === 'ok' ? 'ok' : 'degraded');
    } catch (e) {
      setDetail({ error: String(e) });
      setState('error');
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  const label = {
    loading: 'checking backend…',
    ok: 'backend: ok ✅',
    degraded: 'backend: degraded ⚠️',
    error: 'backend: unreachable ❌',
  }[state];

  const dotColor = {
    loading: '#c9a988',
    ok: '#4caf50',
    degraded: '#e6a817',
    error: '#e5484d',
  }[state];

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />
      <View style={styles.card}>
        <Text style={styles.tag}>NIK_KIT · P0</Text>
        <Text style={styles.logo}>🍽️ Nik_kiT</Text>

        <View style={styles.statusRow}>
          {state === 'loading' ? (
            <ActivityIndicator color="#ff8a3d" />
          ) : (
            <View style={[styles.dot, { backgroundColor: dotColor }]} />
          )}
          <Text style={styles.status}>{label}</Text>
        </View>

        <View style={styles.detailBox}>
          <Text style={styles.detailText}>
            {detail ? JSON.stringify(detail, null, 2) : `GET ${API_BASE_URL}/api/v1/health`}
          </Text>
        </View>

        <Pressable style={styles.button} onPress={check}>
          <Text style={styles.buttonText}>Re-check</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#1b1108',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: '#2a1a0d',
    borderColor: '#4a2f16',
    borderWidth: 1,
    borderRadius: 20,
    padding: 28,
    alignItems: 'center',
  },
  tag: { color: '#ff8a3d', fontWeight: '700', letterSpacing: 2, fontSize: 12 },
  logo: { color: '#fff8f0', fontSize: 32, fontWeight: '800', marginTop: 4 },
  statusRow: { flexDirection: 'row', alignItems: 'center', marginTop: 24, gap: 8 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  status: { color: '#fff8f0', fontSize: 17 },
  detailBox: {
    marginTop: 18,
    width: '100%',
    backgroundColor: '#160d05',
    borderRadius: 12,
    padding: 14,
  },
  detailText: { color: '#ffd9b8', fontSize: 12, fontFamily: 'Courier' },
  button: {
    marginTop: 18,
    backgroundColor: '#ff8a3d',
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 999,
  },
  buttonText: { color: '#2a1400', fontWeight: '800' },
});
