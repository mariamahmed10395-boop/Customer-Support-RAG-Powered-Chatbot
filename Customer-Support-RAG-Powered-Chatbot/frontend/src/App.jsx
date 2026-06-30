import React, { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:8000';

const CATEGORY_COLORS = {
  ORDER: '#6366f1',
  ACCOUNT: '#8b5cf6',
  REFUND: '#34d399',
  PAYMENT: '#fbbf24',
  DELIVERY: '#f97316',
  SHIPPING: '#06b6d4',
  CONTACT: '#ec4899',
  INVOICE: '#14b8a6',
  FEEDBACK: '#a78bfa',
  SUBSCRIPTION: '#f472b6',
  CANCEL: '#f87171',
};

function formatNumber(num) {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
}

function formatCategoryName(name) {
  return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

const ResultCard = ({ result, index }) => {
  const [expanded, setExpanded] = useState(false);
  
  const color = CATEGORY_COLORS[result.category] || '#6b7280';
  const scoreClass = result.similarity >= 70 ? 'high' : result.similarity >= 40 ? 'medium' : 'low';
  const circumference = 2 * Math.PI * 20;
  const offset = circumference - (result.similarity / 100) * circumference;
  const scoreColor = scoreClass === 'high' ? '#34d399' : scoreClass === 'medium' ? '#fbbf24' : '#f87171';
  
  const isLong = result.response.length > 300;

  return (
    <article className="result-card" style={{ '--card-accent': color, animationDelay: `${index * 60}ms` }}>
      <div className="result-card__header">
        <div className="result-card__meta">
          <span className="result-card__category">
            <span className="result-card__category-dot" style={{ background: color }}></span>
            {result.category}
          </span>
          <span className="result-card__intent">{result.intent}</span>
        </div>
        <div className={`result-card__score score--${scoreClass}`}>
          <div className="score-ring">
            <svg viewBox="0 0 48 48">
              <circle className="score-ring__bg" cx="24" cy="24" r="20" />
              <circle className="score-ring__fill" cx="24" cy="24" r="20"
                stroke={scoreColor}
                strokeDasharray={circumference}
                strokeDashoffset={offset} />
            </svg>
            <div className="score-ring__text">
              <span className="result-card__score-value">{Math.round(result.similarity)}</span>
              <span className="result-card__score-label">%</span>
            </div>
          </div>
        </div>
      </div>
      <div className="result-card__question">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline', verticalAlign: '-2px', marginRight: '4px' }}>
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <path d="M12 17h.01" />
        </svg>
        {result.instruction}
      </div>
      <div className={`result-card__answer ${expanded ? 'result-card__answer--expanded' : ''}`}>
        {result.response.split('\n').map((line, i) => (
          <React.Fragment key={i}>
            {line}
            <br />
          </React.Fragment>
        ))}
        {isLong && !expanded && <div className="result-card__answer-fade"></div>}
      </div>
      {isLong && (
        <button className="result-card__toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Show less' : 'Show more'}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {expanded ? <path d="m18 15-6-6-6 6" /> : <path d="m6 9 6 6 6-6" />}
          </svg>
        </button>
      )}
    </article>
  );
};

export default function App() {
  const [stats, setStats] = useState({ entries: 0, categories: 0, intents: 0 });
  const [categories, setCategories] = useState([]);
  const [currentCategory, setCurrentCategory] = useState('ALL');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchInfo, setSearchInfo] = useState(null);
  const [sortOrder, setSortOrder] = useState('relevance');
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/stats`)
      .then(res => res.json())
      .then(data => {
        setStats({
          entries: data.total_entries || 0,
          categories: data.num_categories || 0,
          intents: data.num_intents || 0
        });
      })
      .catch(console.error);

    fetch(`${API_BASE}/api/categories`)
      .then(res => res.json())
      .then(data => setCategories(data))
      .catch(console.error);
  }, []);

  const performSearch = async (overrideQuery = query) => {
    if (!overrideQuery.trim()) return;
    setIsLoading(true);
    setError(false);
    setHasSearched(true);
    setResults([]);
    
    try {
      const res = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: overrideQuery,
          category: currentCategory,
          top_k: 10,
        }),
      });
      const data = await res.json();
      setResults(data.results || []);
      setSearchInfo({
        num_results: data.num_results,
        time_ms: data.search_time_ms
      });
    } catch (e) {
      console.error(e);
      setError(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery);
    performSearch(exampleQuery);
  };

  const sortedResults = [...results].sort((a, b) => {
    if (sortOrder === 'category') {
      return a.category.localeCompare(b.category);
    }
    return b.similarity - a.similarity; // default is relevance
  });

  return (
    <>
      <div className="bg-grid"></div>
      <div className="bg-glow bg-glow--1"></div>
      <div className="bg-glow bg-glow--2"></div>
      <div className="bg-glow bg-glow--3"></div>

      <div className="app">
        <header className="header">
          <div className="header__logo">
            <div className="header__icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
            </div>
            <div>
              <h1 className="header__title">Customer Support RAG</h1>
              <p className="header__subtitle">Semantic Search Engine</p>
            </div>
          </div>
          <div className="header__stats">
            <div className="stat-pill">
              <span className="stat-pill__value">{formatNumber(stats.entries)}</span>
              <span className="stat-pill__label">Entries</span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill__value">{formatNumber(stats.categories)}</span>
              <span className="stat-pill__label">Categories</span>
            </div>
            <div className="stat-pill">
              <span className="stat-pill__value">{formatNumber(stats.intents)}</span>
              <span className="stat-pill__label">Intents</span>
            </div>
          </div>
        </header>

        <section className="search-section">
          <div className="search-box" style={{ borderColor: isLoading ? 'var(--accent-primary)' : '' }}>
            <div className="search-box__icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
            </div>
            <input
              type="text"
              className="search-box__input"
              placeholder="Ask a customer support question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') performSearch(); }}
            />
            {isLoading && (
              <div className="search-box__spinner">
                <div className="spinner"></div>
              </div>
            )}
            <button className="search-box__btn" onClick={() => performSearch()} disabled={isLoading}>
              Search
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14" />
                <path d="m12 5 7 7-7 7" />
              </svg>
            </button>
          </div>

          <div className="examples">
            <span className="examples__label">Try:</span>
            {['Cancel order', 'Track refund', 'Change address', 'Reset password', 'Delivery status', 'Delete account'].map((text, i) => {
              const queries = [
                'How do I cancel my order?',
                'I want to track my refund',
                'How to change my shipping address?',
                'I forgot my password',
                'Where is my delivery?',
                'How to delete my account?'
              ];
              return (
                <button key={i} className="example-chip" onClick={() => handleExampleClick(queries[i])}>
                  {text}
                </button>
              );
            })}
          </div>
        </section>

        <section className="filters">
          <div className="filters__header">
            <h2 className="filters__title">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
              </svg>
              Filter by Category
            </h2>
          </div>
          <div className="filters__chips">
            <button 
              className={`category-chip ${currentCategory === 'ALL' ? 'category-chip--active' : ''}`}
              onClick={() => { setCurrentCategory('ALL'); if (query.trim()) performSearch(query); }}
            >
              <span className="category-chip__dot" style={{ background: 'var(--accent-primary)' }}></span>
              All
            </button>
            {categories.map(cat => {
              const color = CATEGORY_COLORS[cat.name] || '#6b7280';
              return (
                <button 
                  key={cat.name}
                  className={`category-chip ${currentCategory === cat.name ? 'category-chip--active' : ''}`}
                  onClick={() => { setCurrentCategory(cat.name); if (query.trim()) performSearch(query); }}
                >
                  <span className="category-chip__dot" style={{ background: color }}></span>
                  {formatCategoryName(cat.name)}
                  <span className="category-chip__count">{formatNumber(cat.count)}</span>
                </button>
              );
            })}
          </div>
        </section>

        {searchInfo && !error && !isLoading && (
          <div className="results-info">
            <div className="results-info__left">
              <span>{searchInfo.num_results}</span> results
              <span className="results-info__time">({searchInfo.time_ms}ms)</span>
            </div>
            <div className="results-info__right">
              <label className="results-info__sort" htmlFor="sort-select">Sort:</label>
              <select 
                id="sort-select" 
                className="results-info__select"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
              >
                <option value="relevance">Relevance</option>
                <option value="category">Category</option>
              </select>
            </div>
          </div>
        )}

        <section className="results">
          {error && (
            <div className="empty-state">
              <h2 className="empty-state__title" style={{ color: 'var(--accent-danger)' }}>Search Error</h2>
              <p className="empty-state__text">Could not reach the server. Make sure the FastAPI backend is running.</p>
            </div>
          )}
          {!error && !isLoading && hasSearched && sortedResults.length === 0 && (
            <div className="empty-state">
              <div className="empty-state__icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  <path d="M12 7v2" />
                  <path d="M12 13h.01" />
                </svg>
              </div>
              <h2 className="empty-state__title">No results found</h2>
              <p className="empty-state__text">Try a different query or change the category filter.</p>
            </div>
          )}
          {!error && !isLoading && hasSearched && sortedResults.length > 0 && (
            sortedResults.map((result, i) => (
              <ResultCard key={`${result.instruction}-${i}`} result={result} index={i} />
            ))
          )}
          {!hasSearched && !isLoading && (
            <div className="empty-state">
              <div className="empty-state__icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  <path d="M12 7v2" />
                  <path d="M12 13h.01" />
                </svg>
              </div>
              <h2 className="empty-state__title">Ask anything about customer support</h2>
              <p className="empty-state__text">
                Search through <strong>91,000+</strong> customer support Q&A pairs using AI-powered semantic search.
                Type a question or click an example above to get started.
              </p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
