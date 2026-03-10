import { useEffect, useRef, useState } from "react";
import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import { registerDevice } from "@/api/consent";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export function usePushNotifications() {
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [registered, setRegistered] = useState(false);
  const responseListener = useRef<Notifications.EventSubscription>();

  useEffect(() => {
    (async () => {
      if (!Device.isDevice) return;

      const { status: existing } = await Notifications.getPermissionsAsync();
      let final = existing;
      if (existing !== "granted") {
        const { status } = await Notifications.requestPermissionsAsync();
        final = status;
      }
      if (final !== "granted") return;

      try {
        const projectId = Constants.expoConfig?.extra?.eas?.projectId;
        const token = await Notifications.getExpoPushTokenAsync(
          projectId ? { projectId } : undefined
        );
        setExpoPushToken(token.data);

        await registerDevice(token.data, Platform.OS);
        setRegistered(true);
      } catch {
        setRegistered(false);
      }
    })();

    responseListener.current =
      Notifications.addNotificationResponseReceivedListener(() => {
        // User tapped notification - PendingRequestsScreen will refresh on focus
      });

    return () => {
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, []);

  return { expoPushToken, registered };
}
