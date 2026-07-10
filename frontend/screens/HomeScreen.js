// Home — browse the menu (M02). Sections with recipe cards; tap a card → detail.
import { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { getRecipes, getSections, getStoreStatus } from '../config/api';
import { theme } from '../theme';

export default function HomeScreen({ navigation }) {
  const [sections, setSections] = useState([]);
  const [bySection, setBySection] = useState({});
  const [store, setStore] = useState(null); // { is_open, message, reopens_on }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [secs, status] = await Promise.all([getSections(), getStoreStatus()]);
      setStore(status);
      const map = {};
      await Promise.all(
        secs.map(async (s) => {
          map[s.slug] = await getRecipes(s.slug);
        })
      );
      setSections(secs);
      setBySection(map);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (loading) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={theme.accent} size="large" />
      </View>
    );
  }
  if (error) {
    return (
      <View style={[styles.screen, styles.center]}>
        <Text style={styles.error}>Couldn't load the menu.{'\n'}{error}</Text>
        <Pressable style={styles.retry} onPress={load}>
          <Text style={styles.retryText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ paddingBottom: 40 }}>
      <View style={styles.header}>
        <Text style={styles.logo}>🍽️ Nik_kiT</Text>
        <Text style={styles.tagline}>Parathas · Snacks · Sweets</Text>
        <Pressable style={styles.cartBtn} onPress={() => navigation.navigate('Cart')}>
          <Text style={styles.cartBtnTxt}>🛒 Cart</Text>
        </Pressable>
        <Pressable style={styles.aboutBtn} onPress={() => navigation.navigate('AboutChef')}>
          <Text style={styles.aboutTxt}>👩‍🍳 Meet the Chef</Text>
        </Pressable>
      </View>

      {store && !store.is_open && (
        <View style={styles.closedBanner}>
          <Text style={styles.closedTitle}>🚫 We're closed right now</Text>
          <Text style={styles.closedMsg}>
            {store.message || 'Ordering is paused.'}
            {store.reopens_on ? `  ·  Reopens ${store.reopens_on}` : ''}
          </Text>
          <Text style={styles.closedSub}>You can still browse the menu.</Text>
        </View>
      )}

      {sections.map((s) => (
        <View key={s.id} style={styles.section}>
          <Text style={styles.sectionTitle}>{s.name}</Text>
          {(bySection[s.slug] || []).map((r) => (
            <RecipeCard
              key={r.id}
              recipe={r}
              onPress={() => navigation.navigate('Recipe', { id: r.id, name: r.name })}
            />
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

function RecipeCard({ recipe, onPress }) {
  const unavailable = recipe.display_status === 'UNAVAILABLE';
  return (
    <Pressable
      style={[styles.card, unavailable && styles.cardDim]}
      onPress={onPress}
      disabled={unavailable}
    >
      <View style={styles.thumb}>
        {recipe.thumbnail ? (
          <Image source={{ uri: recipe.thumbnail }} style={styles.thumbImg} />
        ) : (
          <Text style={styles.thumbEmoji}>{recipe.is_sweet ? '🍬' : '🥘'}</Text>
        )}
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.cardName}>{recipe.name}</Text>
        <Text style={styles.cardPrice}>₹{recipe.price}</Text>
      </View>
      {unavailable ? (
        <Text style={styles.badge}>Not available</Text>
      ) : (
        <Text style={styles.chevron}>›</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  header: { paddingTop: 64, paddingBottom: 16, paddingHorizontal: 20, alignItems: 'center' },
  cartBtn: { position: 'absolute', right: 16, top: 60, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8 },
  cartBtnTxt: { color: theme.text, fontWeight: '800', fontSize: 13 },
  aboutBtn: { marginTop: 12, backgroundColor: theme.card, borderColor: theme.accent, borderWidth: 1, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8 },
  aboutTxt: { color: theme.accent, fontWeight: '800', fontSize: 13 },
  logo: { color: theme.text, fontSize: 34, fontWeight: '800' },
  tagline: { color: theme.accent, fontSize: 13, fontWeight: '700', letterSpacing: 2, marginTop: 4 },
  closedBanner: { marginHorizontal: 16, marginTop: 4, backgroundColor: '#3a1512', borderColor: theme.bad, borderWidth: 1, borderRadius: 14, padding: 14 },
  closedTitle: { color: theme.bad, fontSize: 16, fontWeight: '800' },
  closedMsg: { color: theme.text, fontSize: 14, marginTop: 4, fontWeight: '600' },
  closedSub: { color: theme.muted, fontSize: 12, marginTop: 6 },
  section: { paddingHorizontal: 16, marginTop: 18 },
  sectionTitle: { color: theme.text, fontSize: 20, fontWeight: '800', marginBottom: 10, marginLeft: 4 },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.card,
    borderColor: theme.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 12,
    marginBottom: 10,
    gap: 12,
  },
  cardDim: { opacity: 0.5 },
  thumb: {
    width: 56, height: 56, borderRadius: 12, backgroundColor: theme.cardAlt,
    alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
  },
  thumbImg: { width: '100%', height: '100%' },
  thumbEmoji: { fontSize: 28 },
  cardName: { color: theme.text, fontSize: 16, fontWeight: '700' },
  cardPrice: { color: theme.accent, fontSize: 15, fontWeight: '700', marginTop: 2 },
  chevron: { color: theme.muted, fontSize: 26, fontWeight: '700' },
  badge: {
    color: theme.bad, fontSize: 11, fontWeight: '800',
    borderColor: theme.bad, borderWidth: 1, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3,
  },
  error: { color: theme.text, textAlign: 'center', marginBottom: 16 },
  retry: { backgroundColor: theme.accent, paddingVertical: 10, paddingHorizontal: 24, borderRadius: 999 },
  retryText: { color: '#2a1400', fontWeight: '800' },
});
