import { useCallback, useEffect, useState } from "react";
import {
  Button,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import {
  getApiKey,
  getBackendUrl,
  getOrgId,
  setApiKey,
  setBackendUrl,
  setOrgId,
  getDefaultBackendUrl,
} from "@/api/config";

export function SettingsScreen() {
  const [apiKey, setApiKeyState] = useState("");
  const [orgId, setOrgIdState] = useState("");
  const [backendUrl, setBackendUrlState] = useState("");

  useEffect(() => {
    (async () => {
      setApiKeyState(await getApiKey());
      setOrgIdState(await getOrgId());
      setBackendUrlState(await getBackendUrl());
    })();
  }, []);

  const save = useCallback(async () => {
    await setApiKey(apiKey);
    await setOrgId(orgId);
    await setBackendUrl(backendUrl);
  }, [apiKey, orgId, backendUrl]);

  return (
    <View style={styles.container}>
      <Text style={styles.label}>API Key</Text>
      <TextInput
        style={styles.input}
        value={apiKey}
        onChangeText={setApiKeyState}
        placeholder="dev-api-key"
        autoCapitalize="none"
      />
      <Text style={styles.label}>Org ID</Text>
      <TextInput
        style={styles.input}
        value={orgId}
        onChangeText={setOrgIdState}
        placeholder="00000000-0000-0000-0000-000000000001"
        autoCapitalize="none"
      />
      <Text style={styles.label}>Backend URL</Text>
      <TextInput
        style={styles.input}
        value={backendUrl}
        onChangeText={setBackendUrlState}
        placeholder={getDefaultBackendUrl()}
        autoCapitalize="none"
      />
      <Button title="Save" onPress={save} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, backgroundColor: "#fff" },
  label: { fontSize: 14, fontWeight: "600", marginTop: 16, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
});
