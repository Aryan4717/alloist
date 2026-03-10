import { useCallback, useEffect, useState } from "react";
import { useFocusEffect } from "@react-navigation/native";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { router } from "expo-router";
import { RequestCard } from "@/components/RequestCard";
import { fetchPending, PendingRequest } from "@/api/consent";

export function PendingRequestsScreen() {
  const [requests, setRequests] = useState<PendingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchPending();
      setRequests(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  const onDecision = useCallback(
    (requestId: string) => {
      setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
    },
    []
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
        <Text style={styles.hint} onPress={() => router.push("/settings")}>
          Check Settings
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.push("/settings")}>
          <Text style={styles.settingsLink}>Settings</Text>
        </Pressable>
      </View>
      <FlatList
        data={requests}
        keyExtractor={(item) => item.request_id}
        renderItem={({ item }) => (
          <RequestCard request={item} onDecision={onDecision} />
        )}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No pending requests</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  header: { padding: 16, alignItems: "flex-end" },
  settingsLink: { color: "#06c", fontSize: 16 },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  error: { color: "#c00", fontSize: 16, textAlign: "center" },
  hint: { color: "#06c", marginTop: 12, fontSize: 14 },
  empty: {
    padding: 48,
    alignItems: "center",
  },
  emptyText: { color: "#666", fontSize: 16 },
});
