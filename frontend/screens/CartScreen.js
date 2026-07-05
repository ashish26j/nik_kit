// Cart (M05) — review items + total, then checkout.
import { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { fetchCart } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

export default function CartScreen({ navigation }) {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const key = await store.get(KEYS.cartKey);
      if (!key) {
        setCart({ items: [], total: '0.00' });
      } else {
        setCart(await fetchCart(key));
      }
    } catch {
      setCart({ items: [], total: '0.00' }); // closed/expired cart → empty
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  if (loading) {
    return <View style={[styles.screen, styles.center]}><ActivityIndicator color={theme.accent} size="large" /></View>;
  }

  const empty = !cart?.items?.length;

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 140 }}>
        <Text style={styles.title}>Your cart</Text>
        {empty ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyEmoji}>🛒</Text>
            <Text style={styles.emptyText}>Your cart is empty.</Text>
            <Pressable style={styles.browse} onPress={() => navigation.navigate('Home')}>
              <Text style={styles.browseTxt}>Browse the menu</Text>
            </Pressable>
          </View>
        ) : (
          cart.items.map((it) => (
            <View key={it.id} style={styles.item}>
              <View style={{ flex: 1 }}>
                <Text style={styles.itemName}>{it.qty} × {it.recipe_name}</Text>
                {it.options?.length > 0 && (
                  <Text style={styles.itemOpts}>
                    {it.options.map((o) => o.label).join(' · ')}
                  </Text>
                )}
              </View>
              <Text style={styles.itemPrice}>₹{it.line_total}</Text>
            </View>
          ))
        )}
      </ScrollView>

      {!empty && (
        <View style={styles.footer}>
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalVal}>₹{cart.total}</Text>
          </View>
          <Pressable style={styles.checkout} onPress={() => navigation.navigate('Checkout')}>
            <Text style={styles.checkoutTxt}>Checkout</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center' },
  title: { color: theme.text, fontSize: 24, fontWeight: '800', marginBottom: 16 },
  item: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, padding: 14, marginBottom: 10 },
  itemName: { color: theme.text, fontSize: 16, fontWeight: '700' },
  itemOpts: { color: theme.muted, fontSize: 13, marginTop: 4 },
  itemPrice: { color: theme.accent, fontSize: 16, fontWeight: '800' },
  emptyBox: { alignItems: 'center', marginTop: 60, gap: 12 },
  emptyEmoji: { fontSize: 56 },
  emptyText: { color: theme.muted, fontSize: 16 },
  browse: { backgroundColor: theme.accent, borderRadius: 999, paddingVertical: 10, paddingHorizontal: 22, marginTop: 8 },
  browseTxt: { color: '#2a1400', fontWeight: '800' },
  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, padding: 16, backgroundColor: theme.card, borderTopColor: theme.border, borderTopWidth: 1 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  totalLabel: { color: theme.text, fontSize: 18, fontWeight: '700' },
  totalVal: { color: theme.accent, fontSize: 20, fontWeight: '800' },
  checkout: { backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  checkoutTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
});
