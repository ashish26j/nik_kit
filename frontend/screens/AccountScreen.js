// Account (M13) — token-gated My Orders + Profile; Email-OTP restore on a new device.
import { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  getMe,
  getMyOrders,
  requestOtp,
  updateMe,
  verifyOtp,
} from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

const STATUS_LABEL = {
  PLACED: 'Placed',
  PAYMENT_SUBMITTED: 'Payment under review',
  PAYMENT_REJECTED: 'Re-upload payment',
  PAYMENT_CONFIRMED: 'Accepted',
  ACCEPTED: 'Accepted',
  PREPARING: 'Preparing',
  READY_FOR_PICKUP: 'Ready to pick up',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
};

export default function AccountScreen({ navigation }) {
  const [token, setToken] = useState(null);
  const [me, setMe] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // profile edit
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name: '', email: '' });

  // OTP restore
  const [otpEmail, setOtpEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const t = await store.get(KEYS.token);
      setToken(t);
      if (t) {
        const [profile, list] = await Promise.all([getMe(t), getMyOrders(t)]);
        setMe(profile);
        setForm({ first_name: profile.first_name, email: profile.email });
        setOrders(list.sort((a, b) => b.id - a.id));
      }
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const saveProfile = async () => {
    setBusy(true);
    setError(null);
    try {
      const updated = await updateMe(token, form);
      setMe(updated);
      setEditing(false);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  const logout = async () => {
    await store.del(KEYS.token);
    await store.del(KEYS.profile);
    setToken(null);
    setMe(null);
    setOrders([]);
  };

  const sendCode = async () => {
    setBusy(true);
    setError(null);
    try {
      await requestOtp(otpEmail.trim());
      setOtpSent(true);
    } catch (e) {
      setError(e.message || 'No account found for that email.');
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await verifyOtp(otpEmail.trim(), otpCode.trim());
      await store.set(KEYS.token, res.token);
      await store.set(KEYS.profile, JSON.stringify(res.user));
      setOtpSent(false);
      setOtpCode('');
      await load();
    } catch (e) {
      setError(e.message || 'Invalid or expired code.');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <View style={[styles.screen, styles.center]}><ActivityIndicator color={theme.accent} size="large" /></View>;
  }

  // --- Not signed in on this device → Email-OTP restore ---
  if (!token) {
    return (
      <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20 }}>
        <Text style={styles.title}>Your account</Text>
        <Text style={styles.note}>
          Placed an order before? Restore your account with your email — we'll send a code.
          No password needed.
        </Text>

        <Text style={styles.label}>Email</Text>
        <TextInput
          style={styles.input}
          value={otpEmail}
          onChangeText={setOtpEmail}
          placeholder="you@example.com"
          placeholderTextColor={theme.muted}
          autoCapitalize="none"
          keyboardType="email-address"
        />

        {otpSent && (
          <>
            <Text style={styles.label}>Code (check your email)</Text>
            <TextInput
              style={styles.input}
              value={otpCode}
              onChangeText={setOtpCode}
              placeholder="6-digit code"
              placeholderTextColor={theme.muted}
              keyboardType="number-pad"
            />
          </>
        )}

        {!!error && <Text style={styles.error}>{error}</Text>}

        <Pressable
          style={[styles.primary, busy && { opacity: 0.6 }]}
          onPress={otpSent ? verifyCode : sendCode}
          disabled={busy}
        >
          <Text style={styles.primaryTxt}>
            {busy ? 'Please wait…' : otpSent ? 'Verify & restore' : 'Send code'}
          </Text>
        </Pressable>

        <Text style={styles.hint}>New here? Just place an order — your account is created automatically.</Text>
      </ScrollView>
    );
  }

  // --- Signed in (token present) → Profile + My Orders ---
  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
      <Text style={styles.title}>Profile</Text>
      <View style={styles.card}>
        {editing ? (
          <>
            <Text style={styles.label}>First name</Text>
            <TextInput style={styles.input} value={form.first_name} onChangeText={(v) => setForm((f) => ({ ...f, first_name: v }))} placeholderTextColor={theme.muted} />
            <Text style={styles.label}>Email</Text>
            <TextInput style={styles.input} value={form.email} onChangeText={(v) => setForm((f) => ({ ...f, email: v }))} autoCapitalize="none" keyboardType="email-address" placeholderTextColor={theme.muted} />
            <Text style={styles.phone}>📱 {me.phone} · your account ID (not editable)</Text>
            <View style={styles.row}>
              <Pressable style={[styles.primary, styles.flex1, busy && { opacity: 0.6 }]} onPress={saveProfile} disabled={busy}>
                <Text style={styles.primaryTxt}>{busy ? 'Saving…' : 'Save'}</Text>
              </Pressable>
              <Pressable style={styles.ghost} onPress={() => { setEditing(false); setForm({ first_name: me.first_name, email: me.email }); }}>
                <Text style={styles.ghostTxt}>Cancel</Text>
              </Pressable>
            </View>
          </>
        ) : (
          <>
            <Text style={styles.name}>{me.first_name}</Text>
            <Text style={styles.meta}>✉️ {me.email}</Text>
            <Text style={styles.meta}>📱 {me.phone}</Text>
            <Pressable style={styles.editBtn} onPress={() => setEditing(true)}>
              <Text style={styles.editTxt}>Edit profile</Text>
            </Pressable>
          </>
        )}
      </View>

      {!!error && <Text style={styles.error}>{error}</Text>}

      <Text style={[styles.title, { marginTop: 24 }]}>My Orders</Text>
      {orders.length === 0 ? (
        <Text style={styles.note}>No orders yet.</Text>
      ) : (
        orders.map((o) => (
          <Pressable key={o.id} style={styles.orderRow} onPress={() => navigation.navigate('Tracking', { orderId: o.id })}>
            <View style={{ flex: 1 }}>
              <Text style={styles.orderCode}>{o.code}</Text>
              <Text style={styles.orderTotal}>₹{o.total}</Text>
            </View>
            <Text style={[styles.statusChip, o.status === 'COMPLETED' && styles.statusDone, o.status === 'CANCELLED' && styles.statusBad]}>
              {STATUS_LABEL[o.status] || o.status}
            </Text>
            <Text style={styles.chevron}>›</Text>
          </Pressable>
        ))
      )}

      <Pressable style={styles.logout} onPress={logout}>
        <Text style={styles.logoutTxt}>Sign out on this device</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  title: { color: theme.text, fontSize: 22, fontWeight: '800', marginBottom: 12 },
  note: { color: theme.muted, fontSize: 14, lineHeight: 20, marginBottom: 16 },
  hint: { color: theme.muted, fontSize: 13, marginTop: 18, textAlign: 'center' },
  label: { color: theme.text, fontSize: 13, fontWeight: '700', marginBottom: 6, marginTop: 10 },
  input: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 12, color: theme.text, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  card: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 16, padding: 16 },
  name: { color: theme.text, fontSize: 20, fontWeight: '800' },
  meta: { color: theme.muted, fontSize: 14, marginTop: 6 },
  phone: { color: theme.muted, fontSize: 12, marginTop: 10 },
  editBtn: { marginTop: 14, alignSelf: 'flex-start', backgroundColor: theme.cardAlt, borderRadius: 999, paddingHorizontal: 18, paddingVertical: 8 },
  editTxt: { color: theme.accent, fontWeight: '800', fontSize: 13 },
  row: { flexDirection: 'row', gap: 10, marginTop: 14, alignItems: 'center' },
  flex1: { flex: 1 },
  primary: { backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 18 },
  primaryTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
  ghost: { paddingVertical: 15, paddingHorizontal: 18, marginTop: 18 },
  ghostTxt: { color: theme.muted, fontWeight: '800' },
  orderRow: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, padding: 14, marginBottom: 10 },
  orderCode: { color: theme.text, fontSize: 16, fontWeight: '800' },
  orderTotal: { color: theme.accent, fontSize: 14, fontWeight: '700', marginTop: 2 },
  statusChip: { color: theme.muted, fontSize: 12, fontWeight: '800', borderColor: theme.border, borderWidth: 1, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, overflow: 'hidden' },
  statusDone: { color: '#4caf50', borderColor: '#4caf50' },
  statusBad: { color: theme.bad, borderColor: theme.bad },
  chevron: { color: theme.muted, fontSize: 24, fontWeight: '700' },
  logout: { marginTop: 26, alignItems: 'center', paddingVertical: 12 },
  logoutTxt: { color: theme.bad, fontWeight: '800' },
  error: { color: theme.bad, textAlign: 'center', marginTop: 12 },
});
