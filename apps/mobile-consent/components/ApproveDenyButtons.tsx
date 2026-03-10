import { useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { submitDecision } from "@/api/consent";

interface ApproveDenyButtonsProps {
  requestId: string;
  onDecision: (requestId: string) => void;
}

export function ApproveDenyButtons({ requestId, onDecision }: ApproveDenyButtonsProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = async (decision: "approve" | "deny") => {
    setLoading(true);
    setError(null);
    try {
      await submitDecision(requestId, decision);
      onDecision(requestId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <View style={styles.row}>
        <TouchableOpacity
          style={[styles.button, styles.approve]}
          onPress={() => handle("approve")}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.buttonText}>Approve</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.button, styles.deny]}
          onPress={() => handle("deny")}
          disabled={loading}
        >
          <Text style={styles.buttonText}>Deny</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 8 },
  row: { flexDirection: "row", gap: 12 },
  button: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  approve: { backgroundColor: "#0a6" },
  deny: { backgroundColor: "#c00" },
  buttonText: { color: "#fff", fontWeight: "600", fontSize: 16 },
  error: { color: "#c00", fontSize: 12, marginBottom: 8 },
});
