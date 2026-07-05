// Checkout (M01 light registration + M05 place order).
// If not yet registered, capture First name / Email / Phone (no password), then
// place the order → PLACED.
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { placeOrder, registerClient } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

export default function CheckoutScreen({ navigation }) {
  const [token, setToken] = useState(null);
  const [ready, setReady] = useState(false);
  const [form, setForm] = useState({ first_name: '', email: '', phone: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const t = await store.get(KEYS.token);
      setToken(t);
      const p = await store.get(KEYS.profile);
      if (p) setForm(JSON.parse(p));
      setReady(true);
    })();
  }, []);

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  const onPlace = async () => {
    setBusy(true);
    setError(null);
    try {
      let t = token;
      if (!t) {
        const res = await registerClient(form);
        t = res.token;
        await store.set(KEYS.token, t);
        await store.set(KEYS.profile, JSON.stringify(form));
        setToken(t);
      }
      const cartKey = await store.get(KEYS.cartKey);
      const order = await placeOrder(cartKey, t);
      await store.del(KEYS.cartKey); // order placed → cart consumed
      navigation.replace('OrderPlaced', { order });
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  if (!ready) {
    return <View style={[styles.screen, styles.center]}><ActivityIndicator color={theme.accent} size="large" /></View>;
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 16 }}>
      <Text style={styles.title}>Checkout</Text>

      {token ? (
        <Text style={styles.note}>You're registered — just confirm your order.</Text>
      ) : (
        <>
          <Text style={styles.note}>Quick details to place your order (no password needed).</Text>
          <Field label="First name" value={form.first_name} onChange={set('first_name')} placeholder="Asha" />
          <Field label="Email" value={form.email} onChange={set('email')} placeholder="asha@example.com" keyboardType="email-address" />
          <Field label="Phone" value={form.phone} onChange={set('phone')} placeholder="+91 98765 43210" keyboardType="phone-pad" />
        </>
      )}

      {!!error && <Text style={styles.error}>{error}</Text>}

      <Pressable style={[styles.place, busy && { opacity: 0.6 }]} onPress={onPlace} disabled={busy}>
        <Text style={styles.placeTxt}>{busy ? 'Placing…' : 'Place order'}</Text>
      </Pressable>
    </ScrollView>
  );
}

function Field({ label, value, onChange, ...rest }) {
  return (
    <View style={{ marginTop: 14 }}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={onChange}
        placeholderTextColor={theme.muted}
        autoCapitalize="none"
        {...rest}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  title: { color: theme.text, fontSize: 24, fontWeight: '800', marginBottom: 8 },
  note: { color: theme.muted, fontSize: 14, marginBottom: 8 },
  label: { color: theme.text, fontSize: 13, fontWeight: '700', marginBottom: 6 },
  input: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 12, color: theme.text, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  error: { color: theme.bad, marginTop: 14 },
  place: { marginTop: 28, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  placeTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
});
