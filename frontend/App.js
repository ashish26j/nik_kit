// Nik_kiT — app entry. P1: browse. P2: cart → checkout → order placed.
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';

import CartScreen from './screens/CartScreen';
import CheckoutScreen from './screens/CheckoutScreen';
import HomeScreen from './screens/HomeScreen';
import OrderPlacedScreen from './screens/OrderPlacedScreen';
import RecipeDetailScreen from './screens/RecipeDetailScreen';
import { theme } from './theme';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: theme.card },
          headerTintColor: theme.text,
          headerTitleStyle: { fontWeight: '800' },
          contentStyle: { backgroundColor: theme.bg },
        }}
      >
        <Stack.Screen name="Home" component={HomeScreen} options={{ headerShown: false }} />
        <Stack.Screen
          name="Recipe"
          component={RecipeDetailScreen}
          options={({ route }) => ({ title: route.params?.name || 'Recipe' })}
        />
        <Stack.Screen name="Cart" component={CartScreen} options={{ title: 'Cart' }} />
        <Stack.Screen name="Checkout" component={CheckoutScreen} options={{ title: 'Checkout' }} />
        <Stack.Screen
          name="OrderPlaced"
          component={OrderPlacedScreen}
          options={{ title: 'Order placed', headerBackVisible: false }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
