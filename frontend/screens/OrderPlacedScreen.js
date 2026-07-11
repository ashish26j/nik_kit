// Order placed (M05 → PLACED). Shows the code + status + fulfilment time.
import { ScrollView, Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '../theme';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
function fmt(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const h = d.getHours();
  const hr12 = ((h + 11) % 12) + 1;
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${DAYS[d.getDay()]} ${hr12}:${m} ${h < 12 ? 'AM' : 'PM'}`;
}

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

      <Text style={styles.fulfil}>
        {order.fulfil_mode === 'ORDER_FOR_LATER'
          ? `🗓️  Scheduled for ${fmt(order.scheduled_for)}`
          : `🍳  Fresh · ready by ${fmt(order.ready_by)}`}
      </Text>

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
  fulfil: { color: theme.accent, fontSize: 14, fontWeight: '800', marginTop: 12 },
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
