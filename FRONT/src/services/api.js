const API_BASE_URL = 'http://localhost:8001/api/v1';

export const analyzeAudio = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/analyze/audio`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }

  return response.json();
};

export const analyzeVideo = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/analyze/video`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }

  return response.json();
};

export const analyzeUrl = async (url) => {
  const response = await fetch(`${API_BASE_URL}/analyze/url`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }

  return response.json();
};

export const checkHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error(`Error: ${response.statusText}`);
  }

  return response.json();
};
