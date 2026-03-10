import { Stack } from "expo-router";
import { usePushNotifications } from "@/hooks/usePushNotifications";

export default function RootLayout() {
  usePushNotifications();
  return (
    <Stack>
      <Stack.Screen
        name="index"
        options={{
          title: "Pending Requests",
          headerRight: () => null,
        }}
      />
      <Stack.Screen name="settings" options={{ title: "Settings" }} />
    </Stack>
  );
}
