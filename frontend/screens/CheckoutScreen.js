// Checkout (M01 light registration + M05 place order).
// If not yet registered, capture First name / Email / Phone (no password), then
// place the order → PLACED.
import { useEffect, useMemo, useState } from 'react';
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

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// A few upcoming pickup slots (11am/2pm/5pm/8pm over the next days), > ~1h ahead.
// Sent as naive local ISO; the backend validates lead time + business closures.
function upcomingSlots() {
  const now = new Date();
  const times = [11, 14, 17, 20];
  const out = [];
  for (let day = 0; day < 4 && out.length < 6; day += 1) {
    for (const h of times) {
      const s = new Date(now);
      s.setDate(now.getDate() + day);
      s.setHours(h, 0, 0, 0);
      if (s.getTime() > now.getTime() + 65 * 60 * 1000) {
        const p = (n) => String(n).padStart(2, '0');
        const iso = `${s.getFullYear()}-${p(s.getMonth() + 1)}-${p(s.getDate())}T${p(h)}:00:00`;
        const hr12 = ((h + 11) % 12) + 1;
        const dayLabel = day === 0 ? 'Today' : day === 1 ? 'Tomorrow' : DAYS[s.getDay()];
        out.push({ iso, label: `${dayLabel}, ${hr12}:00 ${h < 12 ? 'AM' : 'PM'}` });
      }
      if (out.length >= 6) break;
    }
  }
  return out;
}

export default function CheckoutScreen({ navigation }) {
  const [token, setToken] = useState(null);
  const [ready, setReady] = useState(false);
  const [form, setForm] = useState({ first_name: '', email: '', phone: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('ORDER_NOW');
  const [slot, setSlot] = useState(null);
  const slots = useMemo(() => upcomingSlots(), []);

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
      const extra =
        mode === 'ORDER_FOR_LATER'
          ? { fulfil_mode: mode, scheduled_for: slot?.iso }
          : { fulfil_mode: mode };
      const order = await placeOrder(cartKey, t, extra);
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

      <Text style={styles.modeTitle}>When would you like it?</Text>
      <View style={styles.modeRow}>
        <Pressable style={[styles.modeBtn, mode === 'ORDER_NOW' && styles.modeOn]} onPress={() => setMode('ORDER_NOW')}>
          <Text style={[styles.modeTxt, mode === 'ORDER_NOW' && styles.modeTxtOn]}>Order now</Text>
          <Text style={styles.modeSub}>Fresh · ready in ~1 hour</Text>
        </Pressable>
        <Pressable style={[styles.modeBtn, mode === 'ORDER_FOR_LATER' && styles.modeOn]} onPress={() => setMode('ORDER_FOR_LATER')}>
          <Text style={[styles.modeTxt, mode === 'ORDER_FOR_LATER' && styles.modeTxtOn]}>Order for later</Text>
          <Text style={styles.modeSub}>Pick a time</Text>
        </Pressable>
      </View>

      {mode === 'ORDER_FOR_LATER' && (
        <View style={styles.slots}>
          {slots.map((s) => (
            <Pressable key={s.iso} style={[styles.slot, slot?.iso === s.iso && styles.slotOn]} onPress={() => setSlot(s)}>
              <Text style={[styles.slotTxt, slot?.iso === s.iso && styles.slotTxtOn]}>{s.label}</Text>
            </Pressable>
          ))}
        </View>
      )}

      {!!error && <Text style={styles.error}>{error}</Text>}

      <Pressable
        style={[styles.place, (busy || (mode === 'ORDER_FOR_LATER' && !slot)) && { opacity: 0.6 }]}
        onPress={onPlace}
        disabled={busy || (mode === 'ORDER_FOR_LATER' && !slot)}
      >
        <Text style={styles.placeTxt}>
          {busy
            ? 'Placing…'
            : mode === 'ORDER_FOR_LATER'
              ? slot ? `Schedule · ${slot.label}` : 'Pick a time above'
              : 'Place order'}
        </Text>
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
  modeTitle: { color: theme.text, fontSize: 16, fontWeight: '800', marginTop: 24, marginBottom: 10 },
  modeRow: { flexDirection: 'row', gap: 10 },
  modeBtn: { flex: 1, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, padding: 14 },
  modeOn: { borderColor: theme.accent, backgroundColor: theme.cardAlt },
  modeTxt: { color: theme.text, fontSize: 15, fontWeight: '800' },
  modeTxtOn: { color: theme.accent },
  modeSub: { color: theme.muted, fontSize: 12, marginTop: 4 },
  slots: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
  slot: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 10 },
  slotOn: { borderColor: theme.accent, backgroundColor: theme.accent },
  slotTxt: { color: theme.text, fontWeight: '700', fontSize: 13 },
  slotTxtOn: { color: '#2a1400' },
  place: { marginTop: 28, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  placeTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
});
