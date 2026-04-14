import { useState, useEffect, useCallback } from 'react';
import {
  getKeywords, addKeyword, deleteKeyword, toggleKeyword,
  getFavorites, saveFavorite, removeFavorite,
  triggerFetch, getStats,
} from './api';

// ==================== Toast System ====================

function ToastContainer({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>{t.message}</div>
      ))}
    </div>
  );
}

let toastId = 0;

// ==================== AO Detail Modal ====================

function AODetailModal({ ao, onClose }) {
  if (!ao) return null;

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('fr-FR') : '—';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>×</button>
        <h2>{ao.title}</h2>

        <div className="detail-row">
          <span className="label">Référence</span>
          <span>{ao.reference}</span>
        </div>
        <div className="detail-row">
          <span className="label">Source</span>
          <span className={`source-badge ${ao.source}`}>{ao.source}</span>
        </div>
        <div className="detail-row">
          <span className="label">Organisme</span>
          <span>{ao.organisme || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Publication</span>
          <span>{formatDate(ao.date_publication)}</span>
        </div>
        <div className="detail-row">
          <span className="label">Clôture</span>
          <span>{formatDate(ao.date_cloture)}</span>
        </div>
        <div className="detail-row">
          <span className="label">Lieu d'exécution</span>
          <span>{ao.lieu_execution || '—'}</span>
        </div>
        <div className="detail-row">
          <span className="label">Nature</span>
          <span>{ao.nature_marche || '—'}</span>
        </div>
        {ao.montant_estime && (
          <div className="detail-row">
            <span className="label">Montant estimé</span>
            <span>{ao.montant_estime.toLocaleString('fr-FR')} €</span>
          </div>
        )}
        {ao.cpv_codes && (
          <div className="detail-row">
            <span className="label">Codes CPV</span>
            <span>{ao.cpv_codes}</span>
          </div>
        )}
        <div className="detail-row">
          <span className="label">Description</span>
          <span>{ao.description || '—'}</span>
        </div>

        {ao.url && (
          <div style={{ marginTop: 16 }}>
            <a href={ao.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              Voir sur le site source ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

// ==================== Main App ====================

export default function App() {
  // State
  const [keywords, setKeywords] = useState([]);
  const [newKw, setNewKw] = useState('');
  const [newKwCat, setNewKwCat] = useState('');
  const [aos, setAos] = useState([]);         // search results (local) or favorites (from DB)
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [selectedAO, setSelectedAO] = useState(null);
  const [fetchSources, setFetchSources] = useState({ BOAMP: true, DECP: true });
  const [toasts, setToasts] = useState([]);
  const [viewMode, setViewMode] = useState('search'); // 'search' or 'favorites'

  const toast = (message, type = 'info') => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  };

  // Load data
  const loadKeywords = useCallback(async () => {
    try {
      const data = await getKeywords(false);
      setKeywords(data);
    } catch { /* ignore */ }
  }, []);

  const loadFavorites = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFavorites({
        page,
        pageSize,
        source: sourceFilter || undefined,
        search: search || undefined,
      });
      setAos(data.items.map(ao => ({ ...ao, is_favorite: true, db_id: ao.id })));
      setTotal(data.total);
    } catch {
      toast('Erreur lors du chargement des favoris', 'error');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sourceFilter, search]);

  const loadStats = useCallback(async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadKeywords(); loadStats(); }, [loadKeywords, loadStats]);
  useEffect(() => {
    if (viewMode === 'favorites') {
      loadFavorites();
    }
  }, [viewMode, loadFavorites]);

  // Handlers
  const handleAddKeyword = async (e) => {
    e.preventDefault();
    if (!newKw.trim()) return;
    try {
      await addKeyword(newKw.trim(), newKwCat || null);
      setNewKw('');
      setNewKwCat('');
      loadKeywords();
      toast('Mot-clé ajouté', 'success');
    } catch (err) {
      toast(err.message, 'error');
    }
  };

  const handleDeleteKeyword = async (id) => {
    try {
      await deleteKeyword(id);
      loadKeywords();
    } catch { /* ignore */ }
  };

  const handleToggleKeyword = async (id) => {
    try {
      await toggleKeyword(id);
      loadKeywords();
    } catch { /* ignore */ }
  };

  const handleFetch = async (extraKeywords = null) => {
    const sources = Object.entries(fetchSources).filter(([, v]) => v).map(([k]) => k);
    if (sources.length === 0) {
      toast('Sélectionnez au moins une source', 'error');
      return;
    }
    setFetching(true);
    try {
      const result = await triggerFetch(sources, extraKeywords);
      // Display search results locally (not from DB)
      let results = result.results || [];
      if (sourceFilter) {
        results = results.filter(ao => ao.source === sourceFilter);
      }
      setAos(results);
      setTotal(results.length);
      setViewMode('search');
      toast(`${result.stats.fetched} AOs trouvés`, 'success');
    } catch (err) {
      toast(`Erreur: ${err.message}`, 'error');
    } finally {
      setFetching(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    const term = search.trim();
    if (!term) {
      await handleFetch();
      return;
    }
    await handleFetch([term]);
  };

  const handleFavorite = async (e, ao) => {
    e.stopPropagation();
    try {
      if (ao.is_favorite) {
        // Unfavorite → delete from DB
        if (ao.db_id) {
          await removeFavorite(ao.db_id);
        }
        // Update local state
        if (viewMode === 'favorites') {
          // Remove from list in favorites view
          setAos(prev => prev.filter(a => a.reference !== ao.reference));
          setTotal(prev => prev - 1);
        } else {
          // Mark as unfavorited in search results
          setAos(prev => prev.map(a =>
            a.reference === ao.reference ? { ...a, is_favorite: false, db_id: null } : a
          ));
        }
        toast('Retiré des favoris', 'info');
      } else {
        // Favorite → save to DB
        const { is_favorite, db_id, id, is_read, created_at, matched_keywords, ...aoData } = ao;
        const saved = await saveFavorite(aoData);
        // Update local state with DB id
        setAos(prev => prev.map(a =>
          a.reference === ao.reference ? { ...a, is_favorite: true, db_id: saved.id } : a
        ));
        toast('Ajouté aux favoris', 'success');
      }
      loadStats();
    } catch (err) {
      toast(`Erreur: ${err.message}`, 'error');
    }
  };

  const handleClickAO = (ao) => {
    setSelectedAO(ao);
  };

  const switchToFavorites = () => {
    setViewMode('favorites');
    setPage(1);
  };

  const switchToSearch = () => {
    setViewMode('search');
  };

  const formatDate = (d) => d ? new Date(d).toLocaleDateString('fr-FR') : '—';
  const totalPages = viewMode === 'favorites' ? Math.ceil(total / pageSize) : 1;

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <h1><span>📋</span> AO Scraper</h1>

        {/* Stats */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="number">{stats.favorites}</div>
              <div className="label">Favoris</div>
            </div>
            <div className="stat-card">
              <div className="number">{stats.total_keywords}</div>
              <div className="label">Mots-clés</div>
            </div>
          </div>
        )}

        {/* Keywords */}
        <div className="keyword-section">
          <h3>Mots-clés</h3>
          <form className="keyword-input-row" onSubmit={handleAddKeyword}>
            <input
              type="text"
              placeholder="Ex: DevOps, Cloud, Java..."
              value={newKw}
              onChange={(e) => setNewKw(e.target.value)}
            />
            <select value={newKwCat} onChange={(e) => setNewKwCat(e.target.value)}>
              <option value="">Catégorie</option>
              <option value="tech">Tech</option>
              <option value="domain">Domaine</option>
              <option value="skill">Compétence</option>
              <option value="other">Autre</option>
            </select>
            <button type="submit" className="btn btn-primary btn-sm">+</button>
          </form>
          <div className="keyword-list">
            {keywords.map((kw) => (
              <span
                key={kw.id}
                className={`keyword-tag ${kw.is_active ? 'active' : 'inactive'}`}
                onClick={() => handleToggleKeyword(kw.id)}
                title={kw.category ? `Catégorie: ${kw.category}` : 'Cliquer pour activer/désactiver'}
              >
                {kw.word}
                <button className="delete-kw" onClick={(e) => { e.stopPropagation(); handleDeleteKeyword(kw.id); }}>×</button>
              </span>
            ))}
            {keywords.length === 0 && (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-light)' }}>
                Ajoutez des mots-clés pour commencer la veille
              </span>
            )}
          </div>
        </div>

        {/* Fetch */}
        <div className="fetch-section">
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-light)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Récupérer les AOs
          </h3>
          <div className="sources">
            <label>
              <input
                type="checkbox"
                checked={fetchSources.BOAMP}
                onChange={(e) => setFetchSources((s) => ({ ...s, BOAMP: e.target.checked }))}
              />
              BOAMP
            </label>
            <label>
              <input
                type="checkbox"
                checked={fetchSources.DECP}
                onChange={(e) => setFetchSources((s) => ({ ...s, DECP: e.target.checked }))}
              />
              DECP
            </label>
          </div>
          <button className="btn btn-primary" onClick={() => handleFetch()} disabled={fetching}>
            {fetching ? <><span className="spinner" /> Récupération...</> : '🔄 Lancer la recherche'}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        {/* Toolbar */}
        <div className="toolbar">
          <form onSubmit={handleSearch} style={{ flex: 1, minWidth: 200, display: 'flex' }}>
            <input
              className="search-input"
              type="text"
              placeholder="Rechercher sur les plateformes..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              style={{ flex: 1 }}
            />
            <button type="submit" className="btn btn-primary" disabled={fetching} style={{ marginLeft: 6 }}>
              {fetching ? '...' : '🔍'}
            </button>
          </form>
          <div className="filter-group">
            <button
              className={`filter-btn ${!sourceFilter ? 'active' : ''}`}
              onClick={() => { setSourceFilter(''); setPage(1); if (viewMode === 'favorites') loadFavorites(); }}
            >Tous</button>
            <button
              className={`filter-btn ${sourceFilter === 'BOAMP' ? 'active' : ''}`}
              onClick={() => { setSourceFilter('BOAMP'); setPage(1); }}
            >BOAMP</button>
            <button
              className={`filter-btn ${sourceFilter === 'DECP' ? 'active' : ''}`}
              onClick={() => { setSourceFilter('DECP'); setPage(1); }}
            >DECP</button>
          </div>
          <div className="filter-group">
            <button
              className={`filter-btn ${viewMode === 'favorites' ? 'active' : ''}`}
              onClick={() => viewMode === 'favorites' ? switchToSearch() : switchToFavorites()}
            >⭐ Favoris</button>
          </div>
        </div>

        {/* AO list */}
        {loading ? (
          <div className="loading"><span className="spinner" /> Chargement...</div>
        ) : aos.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📭</div>
            <h3>Aucun appel d'offre trouvé</h3>
            <p>
              Ajoutez des mots-clés dans la barre latérale puis cliquez sur
              "Lancer la recherche" pour récupérer des AOs depuis les sources publiques.
            </p>
          </div>
        ) : (
          <>
            <div className="ao-list">
              {aos.map((ao) => (
                <div
                  key={ao.reference}
                  className="ao-card"
                  onClick={() => handleClickAO(ao)}
                >
                  <div className="ao-card-header">
                    <h3>{ao.title}</h3>
                    <span className={`source-badge ${ao.source}`}>{ao.source}</span>
                  </div>
                  <div className="meta">
                    {ao.organisme && <span>🏢 {ao.organisme}</span>}
                    <span>📅 {formatDate(ao.date_publication)}</span>
                    {ao.date_cloture && <span>⏰ Clôture: {formatDate(ao.date_cloture)}</span>}
                    {ao.lieu_execution && <span>📍 {ao.lieu_execution}</span>}
                  </div>
                  {ao.description && <div className="description">{ao.description}</div>}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                    <div className="ao-card-actions">
                      <button
                        className={`icon-btn ${ao.is_favorite ? 'favorited' : ''}`}
                        onClick={(e) => handleFavorite(e, ao)}
                        title={ao.is_favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
                      >
                        {ao.is_favorite ? '★' : '☆'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-outline btn-sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  ← Précédent
                </button>
                <span>Page {page} / {totalPages} ({total} résultats)</span>
                <button
                  className="btn btn-outline btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Suivant →
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Detail modal */}
      <AODetailModal ao={selectedAO} onClose={() => setSelectedAO(null)} />

      {/* Toasts */}
      <ToastContainer toasts={toasts} />
    </div>
  );
}
