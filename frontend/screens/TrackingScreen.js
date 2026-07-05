// Order tracking (M07) — the five-stage lifecycle with the current stage highlighted.
import { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { getTracking } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

const STAGES = ['Order placed', 'Order accepted', 'In preparation', 'Ready to pick up', 'Order completed'];

export default function TrackingScreen({ route }) {
  const { orderId } = route.params;
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const token = await store.get(KEYS.token);
      setData(await getTracking(orderId, token));
    } catch (e) {
      setError(e.message || String(e));
    }
  }, [orderId]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (error) return <View style={[styles.screen, styles.center]}><Text style={styles.error}>{error}</Text></View>;
  if (!data) return <View style={[styles.screen, styles.center]}><ActivityIndicator color={theme.accent} size="large" /></View>;

  const currentIdx = STAGES.indexOf(data.customer_stage);
  const rejected = data.status === 'PAYMENT_REJECTED';
  const submitted = data.status === 'PAYMENT_SUBMITTED';

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20 }}>
      <Text style={styles.title}>Order status</Text>

      {submitted && <Text style={styles.interstitial}>💳 Payment under review — we'll confirm shortly.</Text>}
      {rejected && <Text style={[styles.interstitial, { color: theme.bad }]}>⚠️ Payment not confirmed — please re-upload.</Text>}

      <View style={styles.timeline}>
        {STAGES.map((stage, i) => {
          const done = i <= currentIdx;
          const active = i === currentIdx;
          return (
            <View key={stage} style={styles.row}>
              <View style={[styles.dot, done && styles.dotDone, active && styles.dotActive]}>
                <Text style={styles.dotTxt}>{done ? '✓' : i + 1}</Text>
              </View>
              <Text style={[styles.stageTxt, done && styles.stageDone, active && styles.stageActive]}>{stage}</Text>
            </View>
          );
        })}
      </View>

      <Pressable style={styles.refresh} onPress={load}>
        <Text style={styles.refreshTxt}>Refresh</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  title: { color: theme.text, fontSize: 24, fontWeight: '800', marginBottom: 12 },
  interstitial: { color: theme.muted, fontSize: 14, marginBottom: 16 },
  timeline: { gap: 4 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 10 },
  dot: { width: 34, height: 34, borderRadius: 17, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  dotDone: { backgroundColor: theme.accent, borderColor: theme.accent },
  dotActive: { transform: [{ scale: 1.12 }] },
  dotTxt: { color: theme.bg, fontWeight: '800' },
  stageTxt: { color: theme.muted, fontSize: 16 },
  stageDone: { color: theme.text, fontWeight: '700' },
  stageActive: { color: theme.accent, fontWeight: '800' },
  refresh: { marginTop: 28, alignSelf: 'flex-start', backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 22, paddingVertical: 10 },
  refreshTxt: { color: theme.text, fontWeight: '800' },
  error: { color: theme.bad, textAlign: 'center', padding: 24 },
});
