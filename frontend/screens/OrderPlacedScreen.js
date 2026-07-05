// Order placed (M05 → PLACED). Shows the code + status; lifecycle tracking = P3.
import { ScrollView, Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '../theme';

export default function OrderPlacedScreen({ route, navigation }) {
  const { order } = route.params;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20, alignItems: 'center' }}>
      <Text style={styles.emoji}>🎉</Text>
      <Text style={styles.title}>Order placed!</Text>
      <Text style={styles.code}>{order.code}</Text>
      <View style={styles.statusPill}>
        <Text style={styles.statusTxt}>{order.status}</Text>
      </View>

      <View style={styles.card}>
        {order.items.map((it, i) => (
          <View key={i} style={styles.row}>
            <Text style={styles.itemName}>{it.qty} × {it.recipe_name}</Text>
            <Text style={styles.itemPrice}>₹{it.line_total}</Text>
          </View>
        ))}
        <View style={[styles.row, styles.totalRow]}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalVal}>₹{order.total}</Text>
        </View>
      </View>

      <Pressable style={styles.pay} onPress={() => navigation.replace('Payment', { orderId: order.id })}>
        <Text style={styles.payTxt}>Pay ₹{order.total} by UPI</Text>
      </Pressable>
      <Pressable style={styles.track} onPress={() => navigation.navigate('Tracking', { orderId: order.id })}>
        <Text style={styles.trackTxt}>Track order</Text>
      </Pressable>
      <Pressable style={styles.home} onPress={() => navigation.navigate('Home')}>
        <Text style={styles.homeTxt}>Back to menu</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  emoji: { fontSize: 64, marginTop: 24 },
  title: { color: theme.text, fontSize: 26, fontWeight: '800', marginTop: 8 },
  code: { color: theme.accent, fontSize: 20, fontWeight: '800', marginTop: 6, letterSpacing: 1 },
  statusPill: { marginTop: 12, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 6 },
  statusTxt: { color: theme.text, fontWeight: '800', letterSpacing: 1 },
  card: { alignSelf: 'stretch', backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 16, padding: 16, marginTop: 26 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  itemName: { color: theme.text, fontSize: 15 },
  itemPrice: { color: theme.text, fontSize: 15, fontWeight: '700' },
  totalRow: { borderTopColor: theme.border, borderTopWidth: 1, marginTop: 8, paddingTop: 12 },
  totalLabel: { color: theme.text, fontSize: 17, fontWeight: '800' },
  totalVal: { color: theme.accent, fontSize: 19, fontWeight: '800' },
  pay: { alignSelf: 'stretch', marginTop: 26, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  payTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
  track: { alignSelf: 'stretch', marginTop: 12, backgroundColor: theme.card, borderColor: theme.border, borderWidth: 1, borderRadius: 14, paddingVertical: 14, alignItems: 'center' },
  trackTxt: { color: theme.text, fontSize: 15, fontWeight: '800' },
  home: { marginTop: 16, paddingVertical: 12, paddingHorizontal: 28 },
  homeTxt: { color: theme.muted, fontSize: 15, fontWeight: '700' },
});
