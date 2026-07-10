// Rating (M10) — 1–5 stars + optional ≤100-char note on a completed order.
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

import { getRating, submitRating, updateRating } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

export default function RatingScreen({ route, navigation }) {
  const { orderId } = route.params;
  const [stars, setStars] = useState(0);
  const [note, setNote] = useState('');
  const [existing, setExisting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const token = await store.get(KEYS.token);
        const r = await getRating(orderId, token);
        setStars(r.stars);
        setNote(r.note || '');
        setExisting(true);
      } catch (e) {
        // 404 = not rated yet → leave blank
      } finally {
        setLoading(false);
      }
    })();
  }, [orderId]);

  const onSubmit = async () => {
    if (stars < 1) {
      setError('Please tap a star (1–5).');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const token = await store.get(KEYS.token);
      const body = { stars, note };
      if (existing) await updateRating(orderId, token, body);
      else await submitRating(orderId, token, body);
      setDone(true);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={theme.accent} size="large" />
      </View>
    );
  }

  if (done) {
    return (
      <View style={[styles.screen, styles.center]}>
        <Text style={styles.thanksEmoji}>🙏</Text>
        <Text style={styles.thanks}>Thanks for the feedback!</Text>
        <Text style={styles.thanksStars}>{'★'.repeat(stars)}{'☆'.repeat(5 - stars)}</Text>
        <Pressable style={styles.submit} onPress={() => navigation.navigate('Home')}>
          <Text style={styles.submitTxt}>Back to menu</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20, alignItems: 'center' }}>
      <Text style={styles.title}>How was your order?</Text>

      <View style={styles.stars}>
        {[1, 2, 3, 4, 5].map((n) => (
          <Pressable key={n} onPress={() => setStars(n)} hitSlop={6}>
            <Text style={[styles.star, n <= stars && styles.starOn]}>{n <= stars ? '★' : '☆'}</Text>
          </Pressable>
        ))}
      </View>

      <TextInput
        style={styles.input}
        placeholder="Add a note (optional)"
        placeholderTextColor={theme.muted}
        value={note}
        onChangeText={(t) => setNote(t.slice(0, 100))}
        maxLength={100}
        multiline
      />
      <Text style={styles.count}>{note.length}/100</Text>

      {!!error && <Text style={styles.error}>{error}</Text>}

      <Pressable style={[styles.submit, busy && { opacity: 0.6 }]} onPress={onSubmit} disabled={busy}>
        <Text style={styles.submitTxt}>{busy ? 'Saving…' : existing ? 'Update rating' : 'Submit rating'}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  title: { color: theme.text, fontSize: 22, fontWeight: '800', marginTop: 12, marginBottom: 20 },
  stars: { flexDirection: 'row', gap: 8 },
  star: { fontSize: 46, color: theme.border },
  starOn: { color: theme.accent },
  input: {
    marginTop: 28, width: '100%', minHeight: 90, backgroundColor: theme.card,
    borderColor: theme.border, borderWidth: 1, borderRadius: 14, padding: 14,
    color: theme.text, fontSize: 15, textAlignVertical: 'top',
  },
  count: { color: theme.muted, fontSize: 12, alignSelf: 'flex-end', marginTop: 6 },
  submit: { marginTop: 22, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, paddingHorizontal: 28, alignSelf: 'stretch', alignItems: 'center' },
  submitTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
  error: { color: theme.bad, textAlign: 'center', marginTop: 14 },
  thanksEmoji: { fontSize: 64 },
  thanks: { color: theme.text, fontSize: 22, fontWeight: '800', marginTop: 12 },
  thanksStars: { color: theme.accent, fontSize: 28, marginTop: 8, letterSpacing: 4 },
});
