"use client";

import { useState } from "react";
import { useApiKey } from "./ApiKeyProvider";

export function ApiKeyConfig() {
  const { apiKey, setApiKey, isConfigured } = useApiKey();
  const [value, setValue] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setApiKey(value.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (isConfigured) return null;

  return (
    <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
      <h3 className="mb-2 font-medium text-amber-900">Configure API Key</h3>
      <p className="mb-3 text-sm text-amber-800">
        Enter your backend API key (e.g. dev-api-key) to connect to the token and
        policy services.
      </p>
      <div className="flex gap-2">
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="dev-api-key"
          className="rounded-md border border-amber-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <button
          onClick={handleSave}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-hover"
        >
          {saved ? "Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}
