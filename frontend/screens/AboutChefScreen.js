// About Chef (M12) — bio + social icons. Builds a personal connection with customers.
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { getChef } from '../config/api';
import { theme } from '../theme';

export default function AboutChefScreen() {
  const [chef, setChef] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getChef().then(setChef).catch((e) => setError(String(e)));
  }, []);

  if (error) return <Center><Text style={styles.error}>{error}</Text></Center>;
  if (!chef) return <Center><ActivityIndicator color={theme.accent} size="large" /></Center>;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ padding: 24, alignItems: 'center' }}>
      <View style={styles.avatar}>
        {chef.avatar_url ? (
          <Image source={{ uri: chef.avatar_url }} style={styles.avatarImg} />
        ) : (
          <Text style={styles.avatarEmoji}>👩‍🍳</Text>
        )}
      </View>

      <Text style={styles.name}>{chef.name}</Text>
      {!!chef.tagline && <Text style={styles.tagline}>{chef.tagline}</Text>}

      {!!chef.bio && <Text style={styles.bio}>{chef.bio}</Text>}

      {chef.socials?.length > 0 && (
        <View style={styles.socials}>
          {chef.socials.map((s) => (
            <Pressable key={s.handle} style={styles.social} onPress={() => Linking.openURL(s.url)}>
              <Text style={styles.socialIcon}>{s.platform === 'INSTAGRAM' ? '📸' : '🔗'}</Text>
              <Text style={styles.socialTxt}>@{s.handle}</Text>
            </Pressable>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

function Center({ children }) {
  return <View style={[styles.screen, styles.center]}>{children}</View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.bg },
  center: { alignItems: 'center', justifyContent: 'center', padding: 24 },
  avatar: {
    width: 120, height: 120, borderRadius: 60, backgroundColor: theme.card,
    borderColor: theme.border, borderWidth: 1, alignItems: 'center', justifyContent: 'center',
    overflow: 'hidden', marginTop: 8,
  },
  avatarImg: { width: '100%', height: '100%' },
  avatarEmoji: { fontSize: 60 },
  name: { color: theme.text, fontSize: 28, fontWeight: '800', marginTop: 18 },
  tagline: { color: theme.accent, fontSize: 14, fontWeight: '700', marginTop: 4, textAlign: 'center' },
  bio: { color: theme.muted, fontSize: 15, lineHeight: 23, marginTop: 20, textAlign: 'center' },
  socials: { flexDirection: 'row', gap: 12, marginTop: 26, flexWrap: 'wrap', justifyContent: 'center' },
  social: {
    flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: theme.card,
    borderColor: theme.border, borderWidth: 1, borderRadius: 999, paddingHorizontal: 18, paddingVertical: 12,
  },
  socialIcon: { fontSize: 18 },
  socialTxt: { color: theme.text, fontWeight: '800', fontSize: 14 },
  error: { color: theme.bad, textAlign: 'center' },
});
