// Payment (M06) — show UPI QR + amount, then upload the payment screenshot in-app.
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import QRCode from 'react-native-qrcode-svg';
import * as ImagePicker from 'expo-image-picker';

import { getPaymentInfo, uploadProof } from '../config/api';
import { KEYS, store } from '../storage';
import { theme } from '../theme';

export default function PaymentScreen({ route, navigation }) {
  const { orderId } = route.params;
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const token = await store.get(KEYS.token);
      setInfo(await getPaymentInfo(orderId, token));
    } catch (e) {
      setError(e.message || String(e));
    }
  };
  useEffect(() => { load(); }, [orderId]);

  const onUpload = async () => {
    setError(null);
    try {
      const picked = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.6,
      });
      if (picked.canceled) return;
      setBusy(true);
      const asset = picked.assets[0];
      const token = await store.get(KEYS.token);
      const form = new FormData();
      if (Platform.OS === 'web') {
        const blob = await (await fetch(asset.uri)).blob();
        form.append('image', blob, asset.fileName || 'proof.jpg');
      } else {
        form.append('image', { uri: asset.uri, name: 'proof.jpg', type: 'image/jpeg' });
      }
      await uploadProof(orderId, token, form);
      navigation.replace('Tracking', { orderId });
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setBusy(false);
    }
  };

  if (error && !info) return <Center><Text style={styles.error}>{error}</Text></Center>;
  if (!info) return <Center><ActivityIndicator color={theme.accent} size="large" /></Center>;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 20, alignItems: 'center' }}>
      {info.qr_image_url ? (
        <Image source={{ uri: info.qr_image_url }} style={styles.qrImg} resizeMode="contain" />
      ) : (
        <View style={styles.qrBox}>
          <QRCode value={info.qr_payload} size={220} backgroundColor="#ffffff" color="#1b1108" />
        </View>
      )}
      <Text style={styles.caption}>Scan with UPI app to Pay</Text>

      {!!error && <Text style={styles.error}>{error}</Text>}

      <Pressable style={[styles.upload, busy && { opacity: 0.6 }]} onPress={onUpload} disabled={busy}>
        <Text style={styles.uploadTxt}>{busy ? 'Uploading…' : '📸 Upload payment screenshot'}</Text>
      </Pressable>
    </ScrollView>
  );
}

function Center({ children }) {
  return <View style={[styles.screen, styles.center]}>{children}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  qrBox: { backgroundColor: '#fff', padding: 16, borderRadius: 16, marginTop: 24 },
  qrImg: { width: 300, height: 540, marginTop: 8, borderRadius: 16 },
  caption: { color: theme.text, fontSize: 17, fontWeight: '700', marginTop: 12, textAlign: 'center' },
  upload: { marginTop: 24, backgroundColor: theme.accent, borderRadius: 14, paddingVertical: 16, paddingHorizontal: 24, alignSelf: 'stretch', alignItems: 'center' },
  uploadTxt: { color: '#2a1400', fontSize: 16, fontWeight: '800' },
  error: { color: theme.bad, textAlign: 'center', marginTop: 14 },
});
