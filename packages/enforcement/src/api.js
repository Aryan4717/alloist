'use strict';

async function validateTokenRemote(token, apiUrl, apiKey) {
  const base = apiUrl.replace(/\/$/, '');
  const url = `${base}/tokens/validate`;

  const headers = {
    'Content-Type': 'application/json',
  };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ token }),
    });

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    return {
      valid: data.valid,
      status: data.status,
      subject: data.subject || '',
      scopes: data.scopes || [],
    };
  } catch {
    return null;
  }
}

module.exports = { validateTokenRemote };
