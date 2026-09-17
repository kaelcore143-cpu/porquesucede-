/**
 * Sistema de Búsqueda - PorQuéSucede
 * Búsqueda instantánea de artículos con autocompletado
 */

class SearchEngine {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');
        this.searchForm = document.getElementById('search-form');
        this.articles = [];
        this.isSearching = false;
        this.debounceTimer = null;
        this.maxQueryLength = 100; // Maximum allowed query length
        this.errorLog = []; // Store errors for debugging
        
        this.init();
    }

    /**
     * Structured logging for errors with context
     * @param {string} level - Log level (error, warn, info)
     * @param {string} component - Component where error occurred
     * @param {Error|string} error - Error object or message
     * @param {Object} context - Additional context data
     */
    logError(level, component, error, context = {}) {
        const timestamp = new Date().toISOString();
        const errorEntry = {
            timestamp,
            level,
            component,
            message: error instanceof Error ? error.message : error,
            stack: error instanceof Error ? error.stack : null,
            context
        };
        
        this.errorLog.push(errorEntry);
        
        // Keep only last 50 errors to prevent memory issues
        if (this.errorLog.length > 50) {
            this.errorLog.shift();
        }
        
        // Console logging with structured format
        const logMessage = `[${timestamp}] [${level.toUpperCase()}] [${component}] ${errorEntry.message}`;
        
        switch (level) {
            case 'error':
                console.error(logMessage, context);
                break;
            case 'warn':
                console.warn(logMessage, context);
                break;
            default:
                console.log(logMessage, context);
        }
    }

    /**
     * Sanitizes and validates search query input
     * @param {string} query - Raw search query
     * @returns {Object} - { isValid: boolean, sanitized: string, error: string|null }
     */
    sanitizeQuery(query) {
        if (!query || typeof query !== 'string') {
            return {
                isValid: false,
                sanitized: '',
                error: 'Invalid input type'
            };
        }

        // Trim whitespace
        const trimmed = query.trim();

        // Check length limits
        if (trimmed.length === 0) {
            return {
                isValid: false,
                sanitized: '',
                error: 'Empty query'
            };
        }

        if (trimmed.length < 2) {
            return {
                isValid: false,
                sanitized: trimmed,
                error: 'Query too short (minimum 2 characters)'
            };
        }

        if (trimmed.length > this.maxQueryLength) {
            this.logError('warn', 'sanitizeQuery', `Query too long: ${trimmed.length} characters`, { originalLength: trimmed.length });
            return {
                isValid: false,
                sanitized: trimmed.substring(0, this.maxQueryLength),
                error: `Query too long (maximum ${this.maxQueryLength} characters)`
            };
        }

        // Check for dangerous patterns (XSS, injection attempts)
        const dangerousPatterns = [
            /<script[^>]*>.*?<\/script>/gi, // Script tags
            /javascript:/gi, // JavaScript protocol
            /on\w+\s*=/gi, // Event handlers (onclick, onerror, etc.)
            /<iframe[^>]*>/gi, // Iframes
            /<object[^>]*>/gi, // Objects
            /<embed[^>]*>/gi, // Embeds
            /expression\s*\(/gi, // CSS expressions
            /vbscript:/gi, // VBScript
            /data:\s*text\/html/gi, // Data URLs with HTML
            /&#x?[0-9a-f]+;/gi, // HTML entity encoding
            /%3Cscript%3E/gi, // URL-encoded script tags
            /<[^>]*>/g, // Any HTML tags (catch-all)
        ];

        for (const pattern of dangerousPatterns) {
            if (pattern.test(trimmed)) {
                this.logError('warn', 'sanitizeQuery', 'Dangerous pattern detected in query', { pattern: pattern.source });
                return {
                    isValid: false,
                    sanitized: '',
                    error: 'Query contains invalid characters'
                };
            }
        }

        // Check for control characters (except common whitespace)
        const controlCharPattern = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/;
        if (controlCharPattern.test(trimmed)) {
            this.logError('warn', 'sanitizeQuery', 'Control characters detected in query');
            return {
                isValid: false,
                sanitized: '',
                error: 'Query contains invalid characters'
            };
        }

        // Additional sanitization: remove excessive whitespace
        const sanitized = trimmed.replace(/\s+/g, ' ').trim();

        return {
            isValid: true,
            sanitized: sanitized,
            error: null
        };
    }

    async init() {
        try {
            await this.loadArticles();
            this.setupEventListeners();
            this.logError('info', 'init', 'Sistema de búsqueda inicializado correctamente');
        } catch (error) {
            this.logError('error', 'init', error, { phase: 'initialization' });
            
            // Graceful degradation: try to set up event listeners even if article loading fails
            try {
                this.setupEventListeners();
                this.logError('info', 'init', 'Event listeners configured in degraded mode');
            } catch (listenerError) {
                this.logError('error', 'init', listenerError, { phase: 'event_listener_setup' });
                this.showError('Error al cargar el sistema de búsqueda. Por favor, recarga la página.');
                return;
            }
            
            // Show warning but don't completely break functionality
            this.showError('Búsqueda limitada: algunos artículos pueden no estar disponibles');
        }
    }

    async loadArticles() {
        try {
            // En producción, esto podría venir de un JSON generado
            // Por ahora, extraemos del DOM actual
            const articles = document.querySelectorAll('.articulo-card a, .articles-list a');
            
            if (!articles || articles.length === 0) {
                this.logError('warn', 'loadArticles', 'No articles found in DOM', { selector: '.articulo-card a, .articles-list a' });
                this.articles = [];
                return;
            }

            this.articles = Array.from(articles).map(link => {
                try {
                    const title = link.textContent?.trim() || '';
                    const url = link.getAttribute('href');
                    
                    if (!title || !url) {
                        this.logError('warn', 'loadArticles', 'Article missing title or URL', { hasTitle: !!title, hasUrl: !!url });
                        return null;
                    }
                    
                    return {
                        title: title,
                        url: url,
                        category: this.getCategoryFromUrl(url)
                    };
                } catch (e) {
                    this.logError('error', 'loadArticles', e, { phase: 'article_mapping' });
                    return null;
                }
            }).filter(article => article !== null); // Remove null entries

            // Si estamos en una página de categoría, añadir más artículos
            try {
                const categoryArticles = document.querySelectorAll('.articulos-lista .articulo-card h2 a');
                categoryArticles.forEach(link => {
                    try {
                        const url = link.getAttribute('href');
                        const title = link.textContent?.trim();
                        
                        if (!url || !title) return;
                        
                        if (!this.articles.find(a => a.url === url)) {
                            this.articles.push({
                                title: title,
                                url: url,
                                category: this.getCategoryFromUrl(url)
                            });
                        }
                    } catch (e) {
                        this.logError('error', 'loadArticles', e, { phase: 'category_article_processing' });
                    }
                });
            } catch (e) {
                this.logError('error', 'loadArticles', e, { phase: 'category_articles_query' });
                // Continue with articles already loaded
            }

            this.logError('info', 'loadArticles', `Loaded ${this.articles.length} articles successfully`);
        } catch (error) {
            this.logError('error', 'loadArticles', error, { phase: 'article_loading' });
            this.articles = []; // Ensure articles is always an array
            throw error; // Re-throw to allow graceful degradation in init()
        }
    }

    getCategoryFromUrl(url) {
        if (url.includes('/ciencia/')) return 'Ciencia';
        if (url.includes('/cuerpo/')) return 'Cuerpo Humano';
        if (url.includes('/psicologia/')) return 'Psicología';
        if (url.includes('/animales/')) return 'Animales';
        if (url.includes('/tecnologia/')) return 'Tecnología';
        return 'General';
    }

    /**
     * Validates URLs to prevent Open Redirect vulnerabilities
     * Only allows relative URLs or URLs from porquesucede.com domain
     * Blocks dangerous protocols like javascript:, data:, vbscript:, etc.
     * @param {string} url - The URL to validate
     * @returns {boolean} - True if URL is safe, false otherwise
     */
    isValidUrl(url) {
        if (!url || typeof url !== 'string') {
            return false;
        }

        // Trim whitespace
        url = url.trim();

        // Block dangerous protocols
        const dangerousProtocols = [
            'javascript:',
            'data:',
            'vbscript:',
            'file:',
            'ftp:',
            'mailto:',
            'tel:',
            'sms:',
            'chrome:',
            'chrome-extension:',
            'moz-extension:',
            'ms-browser-extension:',
            'about:',
            'blob:',
            'ws:',
            'wss:'
        ];

        // Check if URL starts with any dangerous protocol (case-insensitive)
        const lowerUrl = url.toLowerCase();
        for (const protocol of dangerousProtocols) {
            if (lowerUrl.startsWith(protocol)) {
                console.warn('Blocked dangerous protocol:', protocol);
                return false;
            }
        }

        // Allow relative URLs starting with /
        if (url.startsWith('/')) {
            return true;
        }

        // Allow relative URLs starting with ./ or ../
        if (url.startsWith('./') || url.startsWith('../')) {
            return true;
        }

        // Allow URLs from porquesucede.com domain
        try {
            const urlObj = new URL(url, window.location.origin);
            const allowedDomains = [
                'porquesucede.com',
                'www.porquesucede.com'
            ];

            // Check if the hostname is in the allowlist
            if (allowedDomains.includes(urlObj.hostname)) {
                return true;
            }

            // Also allow same-origin URLs
            if (urlObj.hostname === window.location.hostname) {
                return true;
            }

            console.warn('Blocked URL from unauthorized domain:', urlObj.hostname);
            return false;
        } catch (e) {
            // Invalid URL format
            console.warn('Invalid URL format:', url);
            return false;
        }
    }

    setupEventListeners() {
        try {
            if (!this.searchInput || !this.searchResults) {
                this.logError('error', 'setupEventListeners', 'Required DOM elements not found', {
                    hasInput: !!this.searchInput,
                    hasResults: !!this.searchResults
                });
                return;
            }

            // Búsqueda en tiempo real con debounce
            this.searchInput.addEventListener('input', (e) => {
                try {
                    clearTimeout(this.debounceTimer);
                    this.debounceTimer = setTimeout(() => {
                        this.handleSearch(e.target.value);
                    }, 300);
                } catch (error) {
                    this.logError('error', 'setupEventListeners', error, { eventType: 'input' });
                }
            });

            // Manejar submit del formulario
            if (this.searchForm) {
                this.searchForm.addEventListener('submit', (e) => {
                    try {
                        e.preventDefault();
                        const query = this.searchInput.value.trim();
                        if (query) {
                            this.performSearch(query);
                        }
                    } catch (error) {
                        this.logError('error', 'setupEventListeners', error, { eventType: 'submit' });
                    }
                });
            }

            // Cerrar resultados al hacer click fuera
            document.addEventListener('click', (e) => {
                try {
                    if (this.searchForm && !this.searchForm.contains(e.target)) {
                        this.hideResults();
                    }
                } catch (error) {
                    this.logError('error', 'setupEventListeners', error, { eventType: 'click_outside' });
                }
            });

            // Navegación con teclado
            this.searchInput.addEventListener('keydown', (e) => {
                try {
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        this.navigateResults('down');
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        this.navigateResults('up');
                    } else if (e.key === 'Enter') {
                        e.preventDefault();
                        this.selectCurrentResult();
                    } else if (e.key === 'Escape') {
                        this.hideResults();
                    }
                } catch (error) {
                    this.logError('error', 'setupEventListeners', error, { eventType: 'keydown', key: e.key });
                }
            });

            this.logError('info', 'setupEventListeners', 'Event listeners configured successfully');
        } catch (error) {
            this.logError('error', 'setupEventListeners', error, { phase: 'listener_setup' });
        }
    }

    handleSearch(query) {
        // Use the new sanitization function
        const validation = this.sanitizeQuery(query);
        
        if (!validation.isValid) {
            // For empty or too short queries, just hide results silently
            if (validation.error === 'Empty query' || validation.error.includes('too short')) {
                this.hideResults();
                return;
            }
            
            // For other validation errors, show appropriate feedback
            this.logError('warn', 'handleSearch', validation.error, { query: query.substring(0, 20) });
            this.hideResults();
            return;
        }

        this.performSearch(validation.sanitized);
    }

    performSearch(query) {
        if (this.isSearching) return;
        
        try {
            this.isSearching = true;
            this.showLoading();

            // Simular búsqueda asíncrona
            setTimeout(() => {
                try {
                    const results = this.search(query);
                    this.displayResults(results, query);
                } catch (error) {
                    this.logError('error', 'performSearch', error, { query: query.substring(0, 20) });
                    this.showError('Error al realizar la búsqueda');
                } finally {
                    this.isSearching = false;
                }
            }, 150);
        } catch (error) {
            this.logError('error', 'performSearch', error, { phase: 'search_setup' });
            this.isSearching = false;
            this.showError('Error al iniciar la búsqueda');
        }
    }

    search(query) {
        try {
            if (!this.articles || !Array.isArray(this.articles)) {
                this.logError('error', 'search', 'Articles array is invalid', { articlesType: typeof this.articles });
                return [];
            }

            const normalizedQuery = query.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
            
            return this.articles.filter(article => {
                try {
                    if (!article || !article.title) {
                        return false;
                    }
                    
                    const normalizedTitle = article.title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
                    const normalizedCategory = (article.category || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
                    
                    return normalizedTitle.includes(normalizedQuery) || 
                           normalizedCategory.includes(normalizedQuery);
                } catch (e) {
                    this.logError('error', 'search', e, { article: article?.title?.substring(0, 20) });
                    return false;
                }
            }).slice(0, 8); // Limitar a 8 resultados
        } catch (error) {
            this.logError('error', 'search', error, { phase: 'search_execution' });
            return [];
        }
    }

    displayResults(results, query) {
        try {
            if (!this.searchResults) {
                this.logError('error', 'displayResults', 'Search results container not found');
                return;
            }

            if (!results || !Array.isArray(results)) {
                this.logError('error', 'displayResults', 'Invalid results array', { resultsType: typeof results });
                this.showError('Error al mostrar resultados');
                return;
            }

            if (results.length === 0) {
                this.showNoResults(query);
                return;
            }

            // Clear previous results
            this.searchResults.innerHTML = '';
            
            // Create result items using DOM methods
            results.forEach((article, index) => {
                try {
                    if (!article || !article.title || !article.url) {
                        this.logError('warn', 'displayResults', 'Invalid article data', { index });
                        return;
                    }

                    const resultItem = document.createElement('div');
                    resultItem.className = 'search-result-item';
                    resultItem.setAttribute('data-index', index);
                    resultItem.setAttribute('data-url', article.url);
                    
                    const titleDiv = document.createElement('div');
                    titleDiv.className = 'search-result-title';
                    const highlightedTitle = this.highlightMatch(article.title, query);
                    titleDiv.appendChild(highlightedTitle);
                    
                    const categoryDiv = document.createElement('div');
                    categoryDiv.className = 'search-result-category';
                    categoryDiv.textContent = article.category || 'General';
                    
                    resultItem.appendChild(titleDiv);
                    resultItem.appendChild(categoryDiv);
                    
                    this.searchResults.appendChild(resultItem);
                } catch (e) {
                    this.logError('error', 'displayResults', e, { index, article: article?.title?.substring(0, 20) });
                }
            });

            this.searchResults.style.display = 'block';
            this.attachResultListeners();
        } catch (error) {
            this.logError('error', 'displayResults', error, { phase: 'display_execution' });
            this.showError('Error al mostrar resultados');
        }
    }

    highlightMatch(text, query) {
        // Escape special regex characters in the query to prevent ReDoS
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        
        // Create a document fragment to hold the highlighted text
        const fragment = document.createDocumentFragment();
        let lastIndex = 0;
        let match;
        
        try {
            while ((match = regex.exec(text)) !== null) {
                // Add text before the match
                if (match.index > lastIndex) {
                    fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
                }
                
                // Add the highlighted match
                const mark = document.createElement('mark');
                mark.textContent = match[1];
                fragment.appendChild(mark);
                
                lastIndex = regex.lastIndex;
            }
            
            // Add remaining text after the last match
            if (lastIndex < text.length) {
                fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
            }
            
            return fragment;
        } catch (e) {
            // If regex fails, return plain text
            return document.createTextNode(text);
        }
    }

    attachResultListeners() {
        const items = this.searchResults.querySelectorAll('.search-result-item');
        items.forEach(item => {
            item.addEventListener('click', () => {
                const url = item.getAttribute('data-url');
                if (this.isValidUrl(url)) {
                    window.location.href = url;
                } else {
                    console.error('Blocked redirect to unsafe URL:', url);
                    this.showError('URL no válida');
                }
            });

            item.addEventListener('mouseenter', () => {
                this.setCurrentResult(item);
            });
        });
    }

    navigateResults(direction) {
        const items = this.searchResults.querySelectorAll('.search-result-item');
        if (items.length === 0) return;

        const currentIndex = this.getCurrentResultIndex();
        let newIndex;

        if (direction === 'down') {
            newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        } else {
            newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        }

        this.setCurrentResult(items[newIndex]);
    }

    getCurrentResultIndex() {
        const current = this.searchResults.querySelector('.search-result-item.current');
        return current ? parseInt(current.getAttribute('data-index')) : -1;
    }

    setCurrentResult(item) {
        // Remover clase actual
        const current = this.searchResults.querySelector('.search-result-item.current');
        if (current) current.classList.remove('current');

        // Añadir clase nueva
        item.classList.add('current');
    }

    selectCurrentResult() {
        const current = this.searchResults.querySelector('.search-result-item.current');
        if (current) {
            const url = current.getAttribute('data-url');
            if (this.isValidUrl(url)) {
                window.location.href = url;
            } else {
                console.error('Blocked redirect to unsafe URL:', url);
                this.showError('URL no válida');
            }
        }
    }

    showLoading() {
        try {
            if (!this.searchResults) {
                this.logError('error', 'showLoading', 'Search results container not found');
                return;
            }

            this.searchResults.innerHTML = '';
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'search-loading';
            loadingDiv.textContent = 'Buscando...';
            this.searchResults.appendChild(loadingDiv);
            this.searchResults.style.display = 'block';
        } catch (error) {
            this.logError('error', 'showLoading', error);
        }
    }

    showNoResults(query) {
        try {
            if (!this.searchResults) {
                this.logError('error', 'showNoResults', 'Search results container not found');
                return;
            }

            this.searchResults.innerHTML = '';
            const noResultsDiv = document.createElement('div');
            noResultsDiv.className = 'search-no-results';
            
            // Sanitize the query before displaying to prevent XSS
            const sanitizedQuery = this.escapeHtml(query);
            noResultsDiv.textContent = `No se encontraron resultados para "${sanitizedQuery}"`;
            
            this.searchResults.appendChild(noResultsDiv);
            this.searchResults.style.display = 'block';
        } catch (error) {
            this.logError('error', 'showNoResults', error);
        }
    }

    showError(message) {
        try {
            if (!this.searchResults) {
                this.logError('error', 'showError', 'Search results container not found');
                return;
            }

            this.searchResults.innerHTML = '';
            const errorDiv = document.createElement('div');
            errorDiv.className = 'search-error';
            
            // Sanitize the error message
            const sanitizedMessage = this.escapeHtml(message);
            errorDiv.textContent = sanitizedMessage;
            
            this.searchResults.appendChild(errorDiv);
            this.searchResults.style.display = 'block';
        } catch (error) {
            this.logError('error', 'showError', error);
        }
    }

    /**
     * Escapes HTML special characters to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    escapeHtml(text) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    hideResults() {
        try {
            if (this.searchResults) {
                this.searchResults.style.display = 'none';
                this.searchResults.innerHTML = '';
            }
        } catch (error) {
            this.logError('error', 'hideResults', error);
        }
    }
}

// Estilos CSS para la búsqueda
const searchStyles = `
<style>
.search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    max-height: 400px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
    margin-top: 4px;
}

.search-result-item {
    padding: 12px 16px;
    cursor: pointer;
    transition: background-color 0.2s ease;
    border-bottom: 1px solid var(--border-soft);
}

.search-result-item:last-child {
    border-bottom: none;
}

.search-result-item:hover,
.search-result-item.current {
    background: var(--surface2);
}

.search-result-title {
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
}

.search-result-category {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-family: var(--font-mono);
}

.search-loading,
.search-no-results,
.search-error {
    padding: 16px;
    text-align: center;
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 0.9rem;
}

.search-error {
    color: #ff6b6b;
}

mark {
    background: var(--gold-glow);
    color: var(--gold);
    padding: 1px 2px;
    border-radius: 2px;
}

/* Responsive */
@media (max-width: 640px) {
    .search-results {
        max-height: 300px;
    }
    
    .search-result-item {
        padding: 10px 12px;
    }
}
</style>
`;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Inyectar estilos
        if (!document.getElementById('search-styles')) {
            const styleElement = document.createElement('div');
            styleElement.id = 'search-styles';
            styleElement.innerHTML = searchStyles;
            document.head.appendChild(styleElement);
        }

        // Inicializar motor de búsqueda
        if (document.getElementById('search-form')) {
            new SearchEngine();
        }
    } catch (error) {
        console.error('[SearchEngine] Error during initialization:', error);
        // Try to provide a fallback or user feedback
        const searchForm = document.getElementById('search-form');
        if (searchForm) {
            const errorDiv = document.createElement('div');
            errorDiv.style.color = '#ff6b6b';
            errorDiv.style.padding = '10px';
            errorDiv.style.fontSize = '0.9rem';
            errorDiv.textContent = 'Error: El sistema de búsqueda no está disponible. Por favor, recarga la página.';
            searchForm.parentNode.insertBefore(errorDiv, searchForm.nextSibling);
        }
    }
});
