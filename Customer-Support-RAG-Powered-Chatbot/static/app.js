/**
 * RAG Customer Support — Frontend Application
 * Handles search, filtering, and dynamic result rendering.
 */

// ─── Constants ──────────────────────────────────────────────────────────────
const API_BASE = '';
const DEBOUNCE_MS = 300;
const CATEGORY_COLORS = {
    ORDER:        '#6366f1',
    ACCOUNT:      '#8b5cf6',
    REFUND:       '#34d399',
    PAYMENT:      '#fbbf24',
    DELIVERY:     '#f97316',
    SHIPPING:     '#06b6d4',
    CONTACT:      '#ec4899',
    INVOICE:      '#14b8a6',
    FEEDBACK:     '#a78bfa',
    SUBSCRIPTION: '#f472b6',
    CANCEL:       '#f87171',
};

// ─── State ──────────────────────────────────────────────────────────────────
let currentCategory = 'ALL';
let currentResults = [];
let debounceTimer = null;

// ─── DOM Elements ───────────────────────────────────────────────────────────
const searchInput    = document.getElementById('search-input');
const searchBtn      = document.getElementById('search-btn');
const searchSpinner  = document.getElementById('search-spinner');
const categoryChips  = document.getElementById('category-chips');
const resultsGrid    = document.getElementById('results-grid');
const resultsInfo    = document.getElementById('results-info');
const resultsCount   = document.getElementById('results-count');
const resultsTime    = document.getElementById('results-time');
const emptyState     = document.getElementById('empty-state');
const sortSelect     = document.getElementById('sort-select');
const statEntries    = document.querySelector('#stat-entries .stat-pill__value');
const statCategories = document.querySelector('#stat-categories .stat-pill__value');
const statIntents    = document.querySelector('#stat-intents .stat-pill__value');

// ─── Initialize ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);

async function init() {
    loadStats();
    loadCategories();
    bindEvents();
}

// ─── Data Loading ───────────────────────────────────────────────────────────
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        animateNumber(statEntries, data.total_entries || 0);
        animateNumber(statCategories, data.num_categories || 0);
        animateNumber(statIntents, data.num_intents || 0);
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

async function loadCategories() {
    try {
        const res = await fetch(`${API_BASE}/api/categories`);
        const categories = await res.json();
        renderCategoryChips(categories);
    } catch (e) {
        console.error('Failed to load categories:', e);
    }
}

// ─── Category Chips ─────────────────────────────────────────────────────────
function renderCategoryChips(categories) {
    // Add 'ALL' chip first
    let html = `
        <button class="category-chip category-chip--active" data-category="ALL">
            <span class="category-chip__dot" style="background: var(--accent-primary)"></span>
            All
        </button>
    `;

    categories.forEach(cat => {
        const color = CATEGORY_COLORS[cat.name] || '#6b7280';
        html += `
            <button class="category-chip" data-category="${cat.name}">
                <span class="category-chip__dot" style="background: ${color}"></span>
                ${formatCategoryName(cat.name)}
                <span class="category-chip__count">${formatNumber(cat.count)}</span>
            </button>
        `;
    });

    categoryChips.innerHTML = html;

    // Bind chip events
    categoryChips.querySelectorAll('.category-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            currentCategory = chip.dataset.category;
            categoryChips.querySelectorAll('.category-chip').forEach(c =>
                c.classList.remove('category-chip--active')
            );
            chip.classList.add('category-chip--active');

            // Re-search if there's a query
            if (searchInput.value.trim()) {
                performSearch();
            }
        });
    });
}

// ─── Event Binding ──────────────────────────────────────────────────────────
function bindEvents() {
    searchBtn.addEventListener('click', performSearch);

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });

    // Example chips
    document.querySelectorAll('.example-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            searchInput.value = chip.dataset.query;
            performSearch();
        });
    });

    // Sort
    sortSelect.addEventListener('change', () => {
        sortAndRenderResults();
    });
}

// ─── Search ─────────────────────────────────────────────────────────────────
async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    // UI: loading
    searchSpinner.style.display = 'flex';
    searchBtn.disabled = true;
    emptyState.style.display = 'none';
    resultsGrid.innerHTML = '';
    resultsInfo.style.display = 'none';

    try {
        const res = await fetch(`${API_BASE}/api/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                category: currentCategory,
                top_k: 10,
            }),
        });
        const data = await res.json();

        currentResults = data.results || [];

        // Update info bar
        resultsInfo.style.display = 'flex';
        resultsCount.textContent = data.num_results;
        resultsTime.textContent = `(${data.search_time_ms}ms)`;

        // Render
        sortAndRenderResults();

    } catch (e) {
        console.error('Search failed:', e);
        resultsGrid.innerHTML = `
            <div class="empty-state">
                <h2 class="empty-state__title" style="color: var(--accent-danger)">Search Error</h2>
                <p class="empty-state__text">Could not reach the server. Make sure the FastAPI backend is running.</p>
            </div>
        `;
    } finally {
        searchSpinner.style.display = 'none';
        searchBtn.disabled = false;
    }
}

// ─── Render Results ─────────────────────────────────────────────────────────
function sortAndRenderResults() {
    let results = [...currentResults];
    
    // Ensure unique intents only
    const seenIntents = new Set();
    results = results.filter(r => {
        if (seenIntents.has(r.intent)) return false;
        seenIntents.add(r.intent);
        return true;
    });

    const sort = sortSelect.value;

    if (sort === 'category') {
        results.sort((a, b) => a.category.localeCompare(b.category));
    } else {
        // Ensure sorted by similarity descending
        results.sort((a, b) => b.similarity - a.similarity);
    }
    
    if (resultsCount) {
        resultsCount.textContent = results.length;
    }

    renderResults(results);
}

function renderResults(results) {
    if (!results.length) {
        resultsGrid.innerHTML = '';
        emptyState.style.display = 'block';
        emptyState.querySelector('.empty-state__title').textContent = 'No results found';
        emptyState.querySelector('.empty-state__text').innerHTML =
            'Try a different query or change the category filter.';
        return;
    }

    emptyState.style.display = 'none';

    const html = results.map((r, i) => {
        const color = CATEGORY_COLORS[r.category] || '#6b7280';
        const scoreClass = r.similarity >= 70 ? 'high' : r.similarity >= 40 ? 'medium' : 'low';
        const circumference = 2 * Math.PI * 20; // r=20
        const offset = circumference - (r.similarity / 100) * circumference;
        const scoreColor = scoreClass === 'high' ? '#34d399' : scoreClass === 'medium' ? '#fbbf24' : '#f87171';

        // Truncate long responses
        const response = escapeHtml(r.response);
        const isLong = r.response.length > 300;

        return `
            <article class="result-card" style="--card-accent: ${color}; animation-delay: ${i * 60}ms" data-index="${i}">
                <div class="result-card__header">
                    <div class="result-card__meta">
                        <span class="result-card__category">
                            <span class="result-card__category-dot" style="background: ${color}"></span>
                            ${r.category}
                        </span>
                        <span class="result-card__intent">${r.intent}</span>
                    </div>
                    <div class="result-card__score score--${scoreClass}">
                        <div class="score-ring">
                            <svg viewBox="0 0 48 48">
                                <circle class="score-ring__bg" cx="24" cy="24" r="20"/>
                                <circle class="score-ring__fill" cx="24" cy="24" r="20"
                                    stroke="${scoreColor}"
                                    stroke-dasharray="${circumference}"
                                    stroke-dashoffset="${offset}"/>
                            </svg>
                            <div class="score-ring__text">
                                <span class="result-card__score-value">${Math.round(r.similarity)}</span>
                                <span class="result-card__score-label">%</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="result-card__question">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline; vertical-align: -2px; margin-right: 4px;">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                        <path d="M12 17h.01"/>
                    </svg>
                    ${escapeHtml(r.instruction)}
                </div>
                <div class="result-card__answer" id="answer-${i}">
                    ${response}
                    ${isLong ? `<div class="result-card__answer-fade" id="fade-${i}"></div>` : ''}
                </div>
                ${isLong ? `
                    <button class="result-card__toggle" onclick="toggleAnswer(${i})" id="toggle-${i}">
                        Show more
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m6 9 6 6 6-6"/>
                        </svg>
                    </button>
                ` : ''}
            </article>
        `;
    }).join('');

    resultsGrid.innerHTML = html;
}

// ─── Toggle Answer ──────────────────────────────────────────────────────────
function toggleAnswer(index) {
    const answer = document.getElementById(`answer-${index}`);
    const fade   = document.getElementById(`fade-${index}`);
    const toggle = document.getElementById(`toggle-${index}`);
    const expanded = answer.classList.toggle('result-card__answer--expanded');

    if (fade) fade.style.opacity = expanded ? '0' : '1';
    toggle.innerHTML = expanded
        ? `Show less <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>`
        : `Show more <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>`;
}

// ─── Utilities ──────────────────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}

function formatCategoryName(name) {
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

function formatNumber(num) {
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
}

function animateNumber(el, target) {
    const duration = 1000;
    const start = performance.now();

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const current = Math.round(eased * target);
        el.textContent = formatNumber(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = formatNumber(target);
        }
    }

    requestAnimationFrame(update);
}
