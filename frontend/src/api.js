const API_BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Erreur réseau' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Keywords
export const getKeywords = (activeOnly = true) =>
  request(`/keywords?active_only=${activeOnly}`);

export const addKeyword = (word, category = null) =>
  request('/keywords', {
    method: 'POST',
    body: JSON.stringify({ word, category }),
  });

export const deleteKeyword = (id) =>
  request(`/keywords/${id}`, { method: 'DELETE' });

export const toggleKeyword = (id) =>
  request(`/keywords/${id}/toggle`, { method: 'PATCH' });

// Favoris
export const getFavorites = ({ page = 1, pageSize = 20, source, search } = {}) => {
  const params = new URLSearchParams({ page, page_size: pageSize });
  if (source) params.set('source', source);
  if (search) params.set('search', search);
  return request(`/favorites?${params}`);
};

export const saveFavorite = (aoData) =>
  request('/favorites', {
    method: 'POST',
    body: JSON.stringify(aoData),
  });

export const removeFavorite = (aoId) =>
  request(`/favorites/${aoId}`, { method: 'DELETE' });

// Fetch (search platforms, no DB storage)
export const triggerFetch = (sources = ['BOAMP'], keywords = null, dateFrom = null, dateTo = null) =>
  request('/fetch', {
    method: 'POST',
    body: JSON.stringify({
      sources,
      ...(keywords ? { keywords } : {}),
      ...(dateFrom ? { date_from: dateFrom } : {}),
      ...(dateTo ? { date_to: dateTo } : {}),
    }),
  });

// Stats
export const getStats = () => request('/stats');
