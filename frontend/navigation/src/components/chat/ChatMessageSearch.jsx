import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, X, Filter, User, Calendar, Hash } from 'lucide-react';
import './ChatMessageSearch.css';

/**
 * Chat Message Search Component
 * 
 * Full-text search for chat messages with:
 * - Real-time search
 * - Channel filtering
 * - User filtering
 * - Pagination
 * - Search result highlighting
 */
const ChatMessageSearch = ({ onResultClick }) => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    channel: '',
    user: '',
  });
  const [pagination, setPagination] = useState({
    count: 0,
    limit: 20,
    offset: 0,
    hasNext: false,
  });
  const [showFilters, setShowFilters] = useState(false);
  const searchTimeout = useRef(null);

  // Debounced search
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }

    // Clear previous timeout
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    // Set new timeout
    searchTimeout.current = setTimeout(() => {
      performSearch();
    }, 500); // Wait 500ms after user stops typing

    return () => {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
    };
  }, [query, filters]);

  const performSearch = async (offset = 0) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        q: query,
        limit: pagination.limit.toString(),
        offset: offset.toString(),
      });

      if (filters.channel) {
        params.append('channel', filters.channel);
      }

      if (filters.user) {
        params.append('user', filters.user);
      }

      const response = await fetch(
        `/api/chat/search/?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
  throw new Error('Search failed');
      }

      const data = await response.json();
      
      setResults(data.results);
      setPagination({
        count: data.count,
        limit: data.limit,
        offset: data.offset,
        hasNext: data.next,
      });

    } catch (err) {
      console.error('Search error:', err);
  setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    performSearch(pagination.offset + pagination.limit);
  };

  const handleClearSearch = () => {
    setQuery('');
    setResults([]);
    setFilters({ channel: '', user: '' });
  };

  const highlightText = (text, query) => {
    if (!query || !text) return text;

    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={index}>{part}</mark>
      ) : (
        part
      )
    );
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffHours < 1) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return t('time.minutes_ago', { count: diffMins, defaultValue: '{{count}}m ago' });
    } else if (diffHours < 24) {
      return t('time.hours_ago', { count: diffHours, defaultValue: '{{count}}h ago' });
    } else if (diffDays < 7) {
      return t('time.days_ago', { count: diffDays, defaultValue: '{{count}}d ago' });
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="chat-message-search">
      {/* Search Header */}
      <div className="search-header">
        <h2>{t('chat.search.title', { defaultValue: 'Search Messages' })}</h2>
        <button
          className="filter-toggle"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter size={20} />
          {t('chat.search.filters', { defaultValue: 'Filters' })}
        </button>
      </div>

      {/* Search Input */}
      <div className="search-input-wrapper">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          className="search-input"
          placeholder={t('chat.search.placeholder', { defaultValue: 'Search messages...' })}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && (
          <button className="clear-btn" onClick={handleClearSearch}>
            <X size={20} />
          </button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="search-filters">
          <div className="filter-group">
            <label>
              <Hash size={16} />
              {t('chat.search.channel', { defaultValue: 'Channel' })}
            </label>
            <input
              type="text"
              placeholder={t('chat.search.channel_id_placeholder', { defaultValue: 'Channel ID' })}
              value={filters.channel}
              onChange={(e) =>
                setFilters({ ...filters, channel: e.target.value })
              }
            />
          </div>

          <div className="filter-group">
            <label>
              <User size={16} />
              {t('chat.search.user', { defaultValue: 'User' })}
            </label>
            <input
              type="text"
              placeholder={t('chat.search.user_id_placeholder', { defaultValue: 'User ID' })}
              value={filters.user}
              onChange={(e) =>
                setFilters({ ...filters, user: e.target.value })
              }
            />
          </div>
        </div>
      )}

      {/* Search Stats */}
      {query && results.length > 0 && (
        <div className="search-stats">
          {t('chat.search.found_results', { count: pagination.count, query, defaultValue: 'Found {{count}} result{{count, plural, one {} other {s}}} for "{{query}}"' })}
        </div>
      )}

      {/* Loading State */}
      {loading && results.length === 0 && (
        <div className="search-loading">
          <div className="loading-spinner"></div>
          <p>{t('common.loading')}</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="search-error">
          <p>{t('errors.search_failed', { defaultValue: 'Search failed' })}</p>
          <button onClick={() => performSearch()}>{t('common.retry')}</button>
        </div>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && !error && (
        <div className="no-results">
          <Search size={48} />
          <p>{t('chat.search.no_results', { query, defaultValue: 'No messages found for "{{query}}"' })}</p>
          <p className="hint">{t('chat.search.try_different_keywords', { defaultValue: 'Try different keywords or adjust filters' })}</p>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="search-results">
          {results.map((message) => (
            <div
              key={message.id}
              className="result-item"
              onClick={() => onResultClick && onResultClick(message)}
            >
              <div className="result-header">
                <div className="user-info">
                  {message.user?.avatar ? (
                    <img
                      src={message.user.avatar}
                      alt={message.user.username}
                      className="user-avatar"
                    />
                  ) : (
                    <div className="user-avatar-placeholder">
                      {message.user?.username?.[0]?.toUpperCase() || '?'}
                    </div>
                  )}
                  <span className="username">{message.user?.username || t('common.unknown', { defaultValue: 'Unknown' })}</span>
                </div>

                <div className="message-meta">
                  <span className="channel-name">
                    <Hash size={14} />
                    {message.channel?.name || t('chat.search.channel_with_id', { id: message.channel_id, defaultValue: 'Channel {{id}}' })}
                  </span>
                  <span className="timestamp">
                    <Calendar size={14} />
                    {formatDate(message.created_at)}
                  </span>
                </div>
              </div>

              <div className="result-content">
                {highlightText(message.message, query)}
              </div>

              {message.attachment && (
                <div className="result-attachment">
                  📎 {t('chat.search.has_attachment', { defaultValue: 'Has attachment' })}
                </div>
              )}
            </div>
          ))}

          {/* Load More */}
          {pagination.hasNext && (
            <div className="load-more-wrapper">
              <button
                className="load-more-btn"
                onClick={handleLoadMore}
                disabled={loading}
              >
                {loading ? t('common.loading') : t('common.load_more', { defaultValue: 'Load More' })}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!query && results.length === 0 && (
        <div className="empty-state">
          <Search size={64} />
          <p>{t('chat.search.enter_query', { defaultValue: 'Enter a search query to find messages' })}</p>
          <p className="hint">{t('chat.search.search_across_channels', { defaultValue: 'You can search across all your channels' })}</p>
        </div>
      )}
    </div>
  );
};

export default ChatMessageSearch;
