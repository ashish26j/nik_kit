// Recipe media gallery (M03). Index-based (reliable on web + mobile): the current
// item is rendered; ‹ › arrows and the dots switch it. Images open full-screen on tap;
// VIDEO/LINK items open externally.
import { useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Image } from 'expo-image';

import { theme } from '../theme';

const HERO_H = 240;

export default function MediaCarousel({ media, onOpenImage, fallbackEmoji = '🍽️' }) {
  const [w, setW] = useState(0);
  const [idx, setIdx] = useState(0);

  if (!media || media.length === 0) {
    return (
      <View style={[styles.hero, styles.placeholder]}>
        <Text style={styles.placeholderEmoji}>{fallbackEmoji}</Text>
        <Text style={styles.placeholderTxt}>Photos coming soon</Text>
      </View>
    );
  }

  const last = media.length - 1;
  const cur = Math.min(idx, last);
  const go = (i) => setIdx(Math.max(0, Math.min(last, i)));

  return (
    <View onLayout={(e) => setW(e.nativeEvent.layout.width)}>
      <View style={styles.heroWrap}>
        {w > 0 && <MediaItem item={media[cur]} width={w} onOpenImage={onOpenImage} />}

        {media.length > 1 && cur > 0 && (
          <Pressable style={[styles.arrow, styles.arrowLeft]} onPress={() => go(cur - 1)} hitSlop={8}>
            <Text style={styles.arrowTxt}>‹</Text>
          </Pressable>
        )}
        {media.length > 1 && cur < last && (
          <Pressable style={[styles.arrow, styles.arrowRight]} onPress={() => go(cur + 1)} hitSlop={8}>
            <Text style={styles.arrowTxt}>›</Text>
          </Pressable>
        )}
        {media.length > 1 && (
          <View style={styles.counter}>
            <Text style={styles.counterTxt}>{cur + 1}/{media.length}</Text>
          </View>
        )}
      </View>

      {media.length > 1 && (
        <View style={styles.dots}>
          {media.map((_, i) => (
            <Pressable key={i} onPress={() => go(i)} hitSlop={10}>
              <View style={[styles.dot, i === cur && styles.dotOn]} />
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

function MediaItem({ item, width, onOpenImage }) {
  if (item.kind === 'IMAGE') {
    return (
      <Pressable style={{ width }} onPress={() => onOpenImage?.(item.url)}>
        <Image source={{ uri: item.url }} style={[styles.hero, { width }]} contentFit="cover" transition={250} />
      </Pressable>
    );
  }
  return (
    <Pressable style={[styles.hero, styles.linkTile, { width }]} onPress={() => Linking.openURL(item.url)}>
      <Text style={styles.linkIcon}>{item.kind === 'VIDEO' ? '▶️' : '🔗'}</Text>
      <Text style={styles.linkTxt}>{item.caption || (item.kind === 'VIDEO' ? 'Watch video' : 'Open link')}</Text>
      <Text style={styles.linkSub}>Opens externally ↗</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  heroWrap: { height: HERO_H, position: 'relative' },
  hero: { height: HERO_H, borderRadius: 18, backgroundColor: theme.cardAlt, overflow: 'hidden' },
  placeholder: { alignItems: 'center', justifyContent: 'center' },
  placeholderEmoji: { fontSize: 64 },
  placeholderTxt: { color: theme.muted, fontSize: 13, fontWeight: '700', marginTop: 8 },
  linkTile: { alignItems: 'center', justifyContent: 'center', borderColor: theme.border, borderWidth: 1 },
  linkIcon: { fontSize: 40 },
  linkTxt: { color: theme.text, fontSize: 16, fontWeight: '800', marginTop: 10 },
  linkSub: { color: theme.accent, fontSize: 12, fontWeight: '700', marginTop: 4 },
  arrow: {
    position: 'absolute', top: HERO_H / 2 - 20, width: 40, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.55)', alignItems: 'center', justifyContent: 'center',
  },
  arrowLeft: { left: 10 },
  arrowRight: { right: 10 },
  arrowTxt: { color: '#fff', fontSize: 26, fontWeight: '800', lineHeight: 30, marginTop: -2 },
  counter: {
    position: 'absolute', top: 10, right: 10, backgroundColor: 'rgba(0,0,0,0.55)',
    borderRadius: 999, paddingHorizontal: 10, paddingVertical: 4,
  },
  counterTxt: { color: '#fff', fontSize: 12, fontWeight: '800' },
  dots: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginTop: 12 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: theme.border },
  dotOn: { backgroundColor: theme.accent, width: 20 },
});
