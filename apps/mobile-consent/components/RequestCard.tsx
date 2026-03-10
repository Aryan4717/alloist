import { StyleSheet, Text, View } from "react-native";
import { PendingRequest } from "@/api/consent";
import { ApproveDenyButtons } from "./ApproveDenyButtons";

interface RequestCardProps {
  request: PendingRequest;
  onDecision: (requestId: string) => void;
}

export function RequestCard({ request, onDecision }: RequestCardProps) {
  const actionStr =
    `${request.action?.service ?? ""}.${request.action?.name ?? ""}`.replace(
      /^\./,
      ""
    ) || "unknown";

  const timestamp = request.created_at
    ? new Date(request.created_at).toLocaleString()
    : "";

  return (
    <View style={styles.card}>
      <Text style={styles.agent}>Agent: {request.agent_name}</Text>
      <Text style={styles.action}>Action: {actionStr}</Text>
      <Text style={styles.meta}>
        Metadata: {JSON.stringify(request.metadata ?? request.action?.metadata ?? {})}
      </Text>
      <View style={styles.row}>
        <Text style={styles.risk}>Risk: </Text>
        <Text
          style={[
            styles.riskBadge,
            request.risk_level === "high" && styles.riskHigh,
            request.risk_level === "medium" && styles.riskMedium,
            request.risk_level === "low" && styles.riskLow,
          ]}
        >
          {request.risk_level}
        </Text>
      </View>
      {timestamp ? (
        <Text style={styles.timestamp}>{timestamp}</Text>
      ) : null}
      <ApproveDenyButtons
        requestId={request.request_id}
        onDecision={onDecision}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    margin: 16,
    padding: 16,
    backgroundColor: "#f9f9f9",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#eee",
  },
  agent: { fontSize: 16, fontWeight: "600", marginBottom: 4 },
  action: { fontSize: 14, marginBottom: 4 },
  meta: { fontSize: 12, color: "#666", marginBottom: 8 },
  row: { flexDirection: "row", alignItems: "center", marginBottom: 4 },
  risk: { fontSize: 14 },
  riskBadge: { fontWeight: "600" },
  riskHigh: { color: "#c00" },
  riskMedium: { color: "#c60" },
  riskLow: { color: "#060" },
  timestamp: { fontSize: 12, color: "#999", marginBottom: 12 },
});
