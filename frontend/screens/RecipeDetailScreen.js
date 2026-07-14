// Recipe detail (M02 view + M04 selection). Pick options → add to cart (M05).
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Image } from 'expo-image';

import MediaCarousel from '../components/MediaCarousel';
import { addToCart, getRecipe } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

export default function RecipeDetailScreen({ route, navigation }) {
  const { id } = route.params;
  const [recipe, setRecipe] = useState(null);
  const [error, setError] = useState(null);
  const [sel, setSel] = useState({}); // groupId -> optionId (SINGLE) | [ids] (MULTI)
  const [qty, setQty] = useState(1);
  const [adding, setAdding] = useState(false);
  const [fullImage, setFullImage] = useState(null);

  useEffect(() => {
    getRecipe(id)
      .then((r) => {
        setRecipe(r);
        const init = {};
        for (const g of r.customization || []) {
          if (g.select_type === 'SINGLE') {
            const def = g.options.find((o) => o.is_default) || g.options[0];
            if (def) init[g.group_id] = def.id;
          } else {
            init[g.group_id] = g.options.filter((o) => o.is_default).map((o) => o.id);
          }
        }
        setSel(init);
      })
      .catch((e) => setError(String(e)));
  }, [id]);

  const selectedIds = useMemo(() => {
    const ids = [];
    for (const g of recipe?.customization || []) {
      const v = sel[g.group_id];
      if (g.select_type === 'SINGLE') {
        if (v != null) ids.push(v);
      } else if (Array.isArray(v)) {
        ids.push(...v);
      }
    }
    return ids;
  }, [sel, recipe]);

  const totalPrice = useMemo(() => {
    if (!recipe) return 0;
    let p = Number(recipe.price);
    for (const g of recipe.customization || []) {
      for (const o of g.options) {
        const v = sel[g.group_id];
        const chosen = g.select_type === 'SINGLE' ? v === o.id : (v || []).includes(o.id);
        if (chosen) p += Number(o.price_delta);
      }
    }
    return p * qty;
  }, [recipe, sel, qty]);

  if (error) return <Center><Text style={styles.error}>{error}</Text></Center>;
  if (!recipe) return <Center><ActivityIndicator color={theme.accent} size="large" /></Center>;

  const unavailable = recipe.display_status === 'UNAVAILABLE';

  const pickSingle = (gid, oid) => setSel((s) => ({ ...s, [gid]: oid }));
  const toggleMulti = (gid, oid) =>
    setSel((s) => {
      const cur = new Set(s[gid] || []);
      cur.has(oid) ? cur.delete(oid) : cur.add(oid);
      return { ...s, [gid]: [...cur] };
    });

  const onAdd = async () => {
    setAdding(true);
    setError(null);
    try {
      const cartKey = await store.get(KEYS.cartKey);
      const cart = await addToCart(
        { recipe_id: recipe.id, qty, selected_options: selectedIds },
        cartKey || undefined
      );
      await store.set(KEYS.cartKey, cart.cart_key);
      navigation.navigate('Cart');
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setAdding(false);
    }
  };

  return (
    <>
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 16, paddingBottom: 120 }}>
      <MediaCarousel
        media={recipe.media}
        onOpenImage={setFullImage}
        fallbackEmoji={recipe.is_sweet ? '🍬' : '🥘'}
      />

      <View style={styles.titleRow}>
        <Text style={styles.name}>{recipe.name}</Text>
        <Text style={styles.price}>₹{recipe.price}</Text>
      </View>
      <View style={styles.chips}>
        {recipe.is_sweet && <Text style={styles.chip}>Sweet</Text>}
        {unavailable && <Text style={styles.badge}>Not available</Text>}
      </View>
      {!!recipe.description && <Text style={styles.desc}>{recipe.description}</Text>}

      {!!recipe.default_accompaniment && (
        <Text style={styles.servedWith}>🍽️  Served with {recipe.default_accompaniment} · included</Text>
      )}

      {recipe.chef_style && (
        <Pressable style={styles.chefLink} onPress={() => Linking.openURL(recipe.chef_style.url)}>
          <Text style={styles.chefLinkTxt}>📸  Check Chef style of making</Text>
          <Text style={styles.chefLinkArrow}>↗</Text>
        </Pressable>
      )}

      {recipe.customization?.length > 0 && <Text style={styles.makeItYours}>Make it yours</Text>}
      {recipe.customization?.map((g) => (
        <View key={g.group_id} style={styles.group}>
          <Text style={styles.groupName}>
            {g.name}{g.is_required ? ' *' : ''}
            <Text style={styles.groupMeta}>{'  '}({g.select_type === 'SINGLE' ? 'pick one' : 'pick any'})</Text>
          </Text>
          {g.options.map((o) => {
            const isSingle = g.select_type === 'SINGLE';
            const chosen = isSingle ? sel[g.group_id] === o.id : (sel[g.group_id] || []).includes(o.id);
            return (
              <Pressable
                key={o.id}
                style={styles.option}
                onPress={() => (isSingle ? pickSingle(g.group_id, o.id) : toggleMulti(g.group_id, o.id))}
              >
                <Text style={styles.optionLabel}>
                  {(isSingle ? (chosen ? '◉ ' : '○ ') : (chosen ? '☑ ' : '☐ ')) + o.label}
                </Text>
                {Number(o.price_delta) > 0 && <Text style={styles.optionDelta}>+₹{o.price_delta}</Text>}
              </Pressable>
            );
          })}
        </View>
      ))}

      {recipe.is_orderable ? (
        <>
          <View style={styles.qtyRow}>
            <Text style={styles.qtyLabel}>Quantity</Text>
            <View style={styles.stepper}>
              <Pressable style={styles.stepBtn} onPress={() => setQty((q) => Math.max(1, q - 1))}>
                <Text style={styles.stepTxt}>−</Text>
              </Pressable>
              <Text style={styles.qtyVal}>{qty}</Text>
              <Pressable style={styles.stepBtn} onPress={() => setQty((q) => q + 1)}>
                <Text style={styles.stepTxt}>+</Text>
              </Pressable>
            </View>
          </View>

          {!!error && <Text style={styles.error}>{error}</Text>}

          <Pressable style={[styles.addBtn, adding && { opacity: 0.6 }]} onPress={onAdd} disabled={adding}>
            <Text style={styles.addTxt}>
              {adding ? 'Adding…' : `Add to cart · ₹${totalPrice.toFixed(2)}`}
            </Text>
          </Pressable>
        </>
      ) : (
        <Text style={styles.notOrderable}>
          {unavailable ? 'Currently not available.' : 'Not available for online ordering right now.'}
        </Text>
      )}
    </ScrollView>

    <Modal visible={!!fullImage} transparent animationType="fade" onRequestClose={() => setFullImage(null)}>
      <Pressable style={styles.fullBackdrop} onPress={() => setFullImage(null)}>
        {!!fullImage && <Image source={{ uri: fullImage }} style={styles.fullImg} contentFit="contain" />}
        <Text style={styles.fullClose}>✕  Tap anywhere to close</Text>
      </Pressable>
    </Modal>
    </>
  );
}

function Center({ children }) {
  return <View style={[styles.screen, styles.center]}>{children}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  fullBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.94)', alignItems: 'center', justifyContent: 'center', padding: 12 },
  fullImg: { width: '100%', height: '82%' },
  fullClose: { color: '#fff', fontSize: 14, fontWeight: '800', marginTop: 16 },
  hero: { height: 180, borderRadius: 18, backgroundColor: theme.cardAlt, alignItems: 'center', justifyContent: 'center', overflow: 'hidden', marginBottom: 16 },
  heroImg: { width: '100%', height: '100%' },
  heroEmoji: { fontSize: 72 },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  name: { color: theme.text, fontSize: 24, fontWeight: '800', flex: 1, paddingRight: 12 },
  price: { color: theme.accent, fontSize: 22, fontWeight: '800' },
  chips: { flexDirection: 'row', gap: 8, marginTop: 8 },
  chip: { color: theme.bg, backgroundColor: theme.accent, fontSize: 11, fontWeight: '800', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, overflow: 'hidden' },
  badge: { color: theme.bad, fontSize: 11, fontWeight: '800', borderColor: theme.bad, borderWidth: 1, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3 },
  desc: { color: theme.muted, fontSize: 15, lineHeight: 22, marginTop: 14 },
  notOrderable: { color: theme.muted, fontSize: 14, fontWeight: '700', marginTop: 24, textAlign: 'center' },
  servedWith: { color: theme.text, fontSize: 14, fontWeight: '700', marginTop: 12, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 12 },
  chefLink: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 18, backgroundColor: theme.card, borderColor: theme.accent, borderWidth: 1, borderRadius: 14, paddingVertical: 14, paddingHorizontal: 16 },
  chefLinkTxt: { color: theme.accent, fontSize: 15, fontWeight: '800' },
  chefLinkArrow: { color: theme.accent, fontSize: 18, fontWeight: '800' },
  makeItYours: { color: theme.text, fontSize: 18, fontWeight: '800', marginTop: 26, marginBottom: 8 },
  group: { backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, padding: 14, marginBottom: 12 },
  groupName: { color: theme.text, fontSize: 15, fontWeight: '700', marginBottom: 8 },
  groupMeta: { color: theme.muted, fontSize: 12, fontWeight: '600' },
  option: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  optionLabel: { color: theme.text, fontSize: 15 },
  optionDelta: { color: theme.accent, fontSize: 15, fontWeight: '700' },
  qtyRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 20 },
  qtyLabel: { color: theme.text, fontSize: 16, fontWeight: '700' },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  stepBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  stepTxt: { color: theme.text, fontSize: 22, fontWeight: '800' },
  qtyVal: { color: theme.text, fontSize: 18, fontWeight: '800', minWidth: 24, textAlign: 'center' },
  addBtn: { marginTop: 22, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  addTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
  error: { color: theme.bad, textAlign: 'center', marginTop: 12 },
});
