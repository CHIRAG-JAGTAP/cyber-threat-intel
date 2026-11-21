// Global state
let allThreats = [];
let currentChatThreatId = null;

// Load threats on page load
let currentOffset = 0;
let isLoadingMore = false;
let hasMore = true;

// Build request URL with current filters
function buildThreatUrl(limit, offset) {
    const category = document.getElementById('categoryFilter').value;
    const severity = document.getElementById('severityFilter').value;
    const indiaOnly = document.getElementById('indiaOnlyFilter').checked;
    const todayOnly = document.getElementById('todayOnlyFilter').checked;

    let url = `/api/threats?limit=${limit}&offset=${offset}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    if (severity) url += `&severity=${encodeURIComponent(severity)}`;
    if (indiaOnly) url += `&india_only=true`;
    if (todayOnly) url += `&today_only=true`;

    return url;
}

document.addEventListener('DOMContentLoaded', () => {
    loadThreats();
    loadStats();

    // Allow search on Enter key
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchThreats();
        }
    });

    // NEW: Allow sending chat message with Enter key
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    // Infinite scroll
    window.addEventListener('scroll', () => {
        if (isLoadingMore || !hasMore) return;

        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight;
        const clientHeight = window.innerHeight;

        if (scrollTop + clientHeight >= scrollHeight - 300) {
            loadMoreThreats();
        }
    });
});

// Load threats from API
async function loadThreats() {
    showLoading();
    currentOffset = 0;
    hasMore = true;
    allThreats = [];
    isLoadingMore = false;

    try {
        const url = buildThreatUrl(50, 0);
        const response = await fetch(url);
        const threats = await response.json();
        allThreats = threats;
        currentOffset = threats.length;

        if (threats.length < 50) {
            hasMore = false;
        }

        displayThreats(allThreats);
    } catch (error) {
        console.error('Error loading threats:', error);
        showError('Failed to load threats');
    }
}

// UPDATED: Display threats with chat button
function displayThreats(threats) {
    const threatList = document.getElementById('threatList');

    if (threats.length === 0) {
        threatList.innerHTML = `
            <div class="empty-state">
                <h3>No threats found</h3>
                <p>Try adjusting your filters or click "Scrape Now" to fetch latest data</p>
            </div>
        `;
        return;
    }

    threatList.innerHTML = threats.map(threat => `
        <div class="threat-card">
            <div class="threat-header">
                <div>
                    <h3 class="threat-title">${escapeHtml(threat.title)}</h3>
                    <div class="threat-meta">
                        <span class="badge severity-${threat.severity}">${threat.severity.toUpperCase()}</span>
                        <span class="badge category-badge">${threat.category}</span>
                        ${threat.india_related ? '<span class="badge india-badge">🇮🇳 India</span>' : ''}
                    </div>
                </div>
            </div>
            
            <p class="threat-description">
                ${escapeHtml(threat.description).substring(0, 300)}...
            </p>
            
            ${threat.keywords && threat.keywords.length > 0 ? `
                <div class="threat-keywords">
                    ${threat.keywords.slice(0, 5).map(kw => `
                        <span class="keyword-tag">${escapeHtml(kw)}</span>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="threat-footer">
                <span class="threat-source">📰 ${escapeHtml(threat.source)}</span>
                <div class="threat-dates">
                    <span class="published-date" title="Original published date">🕐 Published on: ${formatPublishedDate(threat.published_date)}</span>
                    <span class="scraped-date" title="Scraped date">📥 ${formatDate(threat.scraped_date)}</span>
                </div>
            </div>
            
            <div class="threat-actions">
                ${threat.url ? `<button class="chat-btn" onclick="window.open('${threat.url}', '_blank')">📄 Read Full</button>` : ''}
                <button class="chat-btn" onclick="openChatModal(${threat.id}, '${escapeHtml(threat.title).replace(/'/g, "\\'")}')">💬 Chat with AI</button>
            </div>
        </div>
    `).join('');
}

async function loadMoreThreats() {
    if (isLoadingMore || !hasMore) return;
    isLoadingMore = true;

    const threatList = document.getElementById('threatList');
    const loader = document.createElement('div');
    loader.className = 'loading-more';
    loader.innerHTML = '<p>🔄 Loading more threats...</p>';
    threatList.appendChild(loader);

    try {
        const url = buildThreatUrl(50, currentOffset);
        const response = await fetch(url);
        const threats = await response.json();

        loader.remove();

        if (threats.length === 0) {
            hasMore = false;
            isLoadingMore = false;
            return;
        }

        allThreats = allThreats.concat(threats);
        appendThreats(threats);
        currentOffset += threats.length;

        if (threats.length < 50) {
            hasMore = false;
        }
    } catch (error) {
        console.error('Error loading more threats:', error);
        loader.remove();
    } finally {
        isLoadingMore = false;
    }
}

function appendThreats(threats) {
    const threatList = document.getElementById('threatList');
    const html = threats.map(threat => `
        <div class="threat-card">
            <div class="threat-header">
                <div>
                    <h3 class="threat-title">${escapeHtml(threat.title)}</h3>
                    <div class="threat-meta">
                        <span class="badge severity-${threat.severity}">${threat.severity.toUpperCase()}</span>
                        <span class="badge category-badge">${threat.category}</span>
                        ${threat.india_related ? '<span class="badge india-badge">🇮🇳 India</span>' : ''}
                    </div>
                </div>
            </div>
            
            <p class="threat-description">
                ${escapeHtml(threat.description).substring(0, 300)}...
            </p>
            
            ${threat.keywords && threat.keywords.length > 0 ? `
                <div class="threat-keywords">
                    ${threat.keywords.slice(0, 5).map(kw => `
                        <span class="keyword-tag">${escapeHtml(kw)}</span>
                    `).join('')}
                </div>
            ` : ''}
            
            <div class="threat-footer">
                <span class="threat-source">📰 ${escapeHtml(threat.source)}</span>
                <div class="threat-dates">
                    <span class="published-date" title="Original published date">🕐 Published on: ${formatPublishedDate(threat.published_date)}</span>
                    <span class="scraped-date" title="Scraped date">📥 ${formatDate(threat.scraped_date)}</span>
                </div>
            </div>
            
            <div class="threat-actions">
                ${threat.url ? `<button class="chat-btn" onclick="window.open('${threat.url}', '_blank')">📄 Read Full</button>` : ''}
                <button class="chat-btn" onclick="openChatModal(${threat.id}, '${escapeHtml(threat.title).replace(/'/g, "\\'")}')">💬 Chat with AI</button>
            </div>
        </div>
    `).join('');

    threatList.insertAdjacentHTML('beforeend', html);
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('totalThreats').textContent = stats.total_threats || 0;
        document.getElementById('indiaThreats').textContent = stats.india_threats || 0;
        document.getElementById('criticalThreats').textContent = stats.by_severity?.critical || 0;
        document.getElementById('todayThreats').textContent = stats.today_threats || 0;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Search threats
async function searchThreats() {
    const query = document.getElementById('searchInput').value;

    if (!query) {
        loadThreats();
        return;
    }

    showLoading();
    hasMore = false; // disable infinite scroll during search

    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const threats = await response.json();
        displayThreats(threats);
    } catch (error) {
        console.error('Error searching threats:', error);
        showError('Search failed');
    }
}

// Filter threats
function filterThreats() {
    loadThreats();
}

// Trigger manual scraping
async function scrapeNow() {
    const button = event.target;
    button.disabled = true;
    button.textContent = '⏳ Scraping...';

    try {
        const response = await fetch('/api/scrape', {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            loadThreats();
            loadStats();
        } else {
            alert('Scraping failed: ' + result.error);
        }
    } catch (error) {
        console.error('Error scraping:', error);
        alert('Scraping failed');
    } finally {
        button.disabled = false;
        button.textContent = '🔄 Scrape Now';
    }
}

//  NEW: Chat Modal Functions
function openChatModal(threatId, threatTitle) {
    currentChatThreatId = threatId;
    const modal = document.getElementById('chatModal');
    const messages = document.getElementById('chatMessages');

    // Reset chat
    messages.innerHTML = `
        <div class="chat-message system">
            <strong>AI Assistant:</strong> Hello! I can help you understand this threat: "${threatTitle}". What would you like to know?
        </div>
    `;

    modal.style.display = 'flex';
    document.getElementById('chatInput').focus();
}

function closeChatModal() {
    document.getElementById('chatModal').style.display = 'none';
    currentChatThreatId = null;
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();

    if (!question || !currentChatThreatId) return;

    // Add user message
    const messages = document.getElementById('chatMessages');
    messages.innerHTML += `
        <div class="chat-message user">
            <strong>You:</strong> ${escapeHtml(question)}
        </div>
    `;

    // Clear input
    input.value = '';

    // Show loading
    messages.innerHTML += `
        <div class="chat-message system loading">
            <strong>AI Assistant:</strong> Thinking...
        </div>
    `;

    // Scroll to bottom
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                threat_id: currentChatThreatId,
                question: question
            })
        });

        const data = await response.json();

        // Remove loading message
        const loadingMsg = messages.querySelector('.loading');
        if (loadingMsg) loadingMsg.remove();

        // Add AI response
        messages.innerHTML += `
            <div class="chat-message assistant">
                <strong>AI Assistant:</strong> ${escapeHtml(data.answer)}
            </div>
        `;

        // Scroll to bottom
        messages.scrollTop = messages.scrollHeight;

    } catch (error) {
        console.error('Chat error:', error);
        const loadingMsg = messages.querySelector('.loading');
        if (loadingMsg) loadingMsg.remove();

        messages.innerHTML += `
            <div class="chat-message error">
                <strong>Error:</strong> Failed to get AI response. Please check your OpenAI API key in config.py
            </div>
        `;
    }
}

// Utility functions
function showLoading() {
    document.getElementById('threatList').innerHTML = `
        <div class="loading">
            <p>🔄 Loading threats...</p>
        </div>
    `;
}

function showError(message) {
    document.getElementById('threatList').innerHTML = `
        <div class="empty-state">
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
}

function formatPublishedDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
