const NOTICIAS_API_BASE_URL = resolveApiBaseUrl(
  'VITE_NOTICIAS_API_URL',
  8001,
  'https://noticias-api-production.up.railway.app',
);
const VIDEO_AUDIO_API_BASE_URL = resolveApiBaseUrl(
  'VITE_VIDEO_AUDIO_API_URL',
  8001,
  'https://video-audio-production.up.railway.app',
);

export const analyzeNewsUrl = async (url) => {
  const response = await fetch(`${NOTICIAS_API_BASE_URL}/api/v1/noticias/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  return parseResponse(response);
};

export const getNewsAnalysis = async (analysisId) => {
  const response = await fetch(`${NOTICIAS_API_BASE_URL}/api/v1/noticias/analysis/${analysisId}`);
  return parseResponse(response);
};

export const askKuybot = async ({ question, news, history }) => {
  const response = await fetch(`${NOTICIAS_API_BASE_URL}/api/v1/noticias/kuybot`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, news, history }),
  });

  return parseResponse(response);
};

export const analyzeAudio = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${VIDEO_AUDIO_API_BASE_URL}/api/v1/analyze/audio`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse(response);
};

export const analyzeVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${VIDEO_AUDIO_API_BASE_URL}/api/v1/analyze/video`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse(response);
};

export const analyzeMediaUrl = async (url) => {
  const response = await fetch(`${VIDEO_AUDIO_API_BASE_URL}/api/v1/analyze/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });

  return parseResponse(response);
};

export const checkVideoAudioHealth = async () => {
  const response = await fetch(`${VIDEO_AUDIO_API_BASE_URL}/api/v1/health`);
  return parseResponse(response);
};

async function parseResponse(response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.detail || data?.error || response.statusText || 'Error de API');
  }
  return data;
}

function resolveApiBaseUrl(envKey, port, productionFallback) {
  const configuredUrl = import.meta.env[envKey];
  if (configuredUrl) return normalizeApiUrl(configuredUrl);
  if (typeof window === 'undefined') return configuredUrl || productionFallback || `http://localhost:${port}`;

  const { protocol, hostname } = window.location;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:${port}`;
  }
  if (hostname.endsWith('.app.github.dev')) {
    return `${protocol}//${hostname.replace('-5173.', `-${port}.`)}`;
  }
  if (hostname.endsWith('.devtunnels.ms')) {
    return `${protocol}//${hostname.replace('-5173.', `-${port}.`)}`;
  }
  if (hostname.includes('5173')) {
    return `${protocol}//${hostname.replace('5173', String(port))}`;
  }

  return configuredUrl || productionFallback || `http://localhost:${port}`;
}

function normalizeApiUrl(url) {
  const cleanUrl = url.replace(/\/$/, '');
  if (/^https?:\/\//i.test(cleanUrl)) return cleanUrl;
  return `https://${cleanUrl}`;
}
