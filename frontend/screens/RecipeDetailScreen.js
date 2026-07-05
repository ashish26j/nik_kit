// Recipe detail (M02) — image, description, price, and read-only customization.
// Actual selection + add-to-cart arrives in P2.
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { getRecipe } from '../config/api';
import { theme } from '../theme';

export default function RecipeDetailScreen({ route }) {
  const { id } = route.params;
  const [recipe, setRecipe] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getRecipe(id).then(setRecipe).catch((e) => setError(String(e)));
  }, [id]);

  if (error) {
    return (
      <View style={[styles.screen, styles.center]}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }
  if (!recipe) {
    return (
      <View style={[styles.screen, styles.center]}>
        <ActivityIndicator color={theme.accent} size="large" />
      </View>
    );
  }

  const unavailable = recipe.display_status === 'UNAVAILABLE';

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 16, paddingBottom: 48 }}>
      <View style={styles.hero}>
        {recipe.images?.length ? (
          <Image source={{ uri: recipe.images[0] }} style={styles.heroImg} />
        ) : (
          <Text style={styles.heroEmoji}>{recipe.is_sweet ? '🍬' : '🥘'}</Text>
        )}
      </View>

      <View style={styles.titleRow}>
        <Text style={styles.name}>{recipe.name}</Text>
        <Text style={styles.price}>₹{recipe.price}</Text>
      </View>

      <View style={styles.chips}>
        {recipe.is_sweet && <Text style={styles.chip}>Sweet</Text>}
        {unavailable && <Text style={styles.badge}>Not available</Text>}
      </View>

      {!!recipe.description && <Text style={styles.desc}>{recipe.description}</Text>}

      {recipe.customization?.length > 0 && (
        <Text style={styles.makeItYours}>Make it yours</Text>
      )}
      {recipe.customization?.map((g) => (
        <View key={g.group_id} style={styles.group}>
          <Text style={styles.groupName}>
            {g.name}
            {g.is_required ? ' *' : ''}
            <Text style={styles.groupMeta}>
              {'  '}({g.select_type === 'SINGLE' ? 'pick one' : 'pick any'})
            </Text>
          </Text>
          {g.options.map((o) => (
            <View key={o.id} style={styles.option}>
              <Text style={styles.optionLabel}>
                {o.is_default ? '◉ ' : '○ '}
                {o.label}
              </Text>
              {Number(o.price_delta) > 0 && (
                <Text style={styles.optionDelta}>+₹{o.price_delta}</Text>
              )}
            </View>
          ))}
        </View>
      ))}

      <View style={styles.cta}>
        <Text style={styles.ctaText}>🛒 Ordering arrives in P2</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  hero: {
    height: 180, borderRadius: 18, backgroundColor: theme.cardAlt,
    alignItems: 'center', justifyContent: 'center', overflow: 'hidden', marginBottom: 16,
  },
  heroImg: { width: '100%', height: '100%' },
  heroEmoji: { fontSize: 72 },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  name: { color: theme.text, fontSize: 24, fontWeight: '800', flex: 1, paddingRight: 12 },
  price: { color: theme.accent, fontSize: 22, fontWeight: '800' },
  chips: { flexDirection: 'row', gap: 8, marginTop: 8 },
  chip: {
    color: theme.bg, backgroundColor: theme.accent, fontSize: 11, fontWeight: '800',
    borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, overflow: 'hidden',
  },
  badge: {
    color: theme.bad, fontSize: 11, fontWeight: '800',
    borderColor: theme.bad, borderWidth: 1, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3,
  },
  desc: { color: theme.muted, fontSize: 15, lineHeight: 22, marginTop: 14 },
  makeItYours: { color: theme.text, fontSize: 18, fontWeight: '800', marginTop: 26, marginBottom: 8 },
  group: {
    backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1,
    borderRadius: 14, padding: 14, marginBottom: 12,
  },
  groupName: { color: theme.text, fontSize: 15, fontWeight: '700', marginBottom: 8 },
  groupMeta: { color: theme.muted, fontSize: 12, fontWeight: '600' },
  option: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5 },
  optionLabel: { color: theme.text, fontSize: 14 },
  optionDelta: { color: theme.accent, fontSize: 14, fontWeight: '700' },
  cta: {
    marginTop: 24, backgroundColor: theme.cardAlt, borderRadius: 14,
    paddingVertical: 16, alignItems: 'center',
  },
  ctaText: { color: theme.muted, fontSize: 14, fontWeight: '700' },
  error: { color: theme.bad, textAlign: 'center' },
});
