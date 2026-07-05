// Cross-platform key/value storage (web + native) for the client token + cart key.
import AsyncStorage from '@react-native-async-storage/async-storage';

export const KEYS = {
  token: 'nk_token',
  cartKey: 'nk_cart_key',
  profile: 'nk_profile',
};

export const store = {
  get: (k) => AsyncStorage.getItem(k),
  set: (k, v) => AsyncStorage.setItem(k, v ?? ''),
  del: (k) => AsyncStorage.removeItem(k),
};
