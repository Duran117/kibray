import React, { useState, useEffect, useRef } from 'react';
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
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="chat-message-search">
      {/* Search Header */}
      <div className="search-header">
        <h2>Search Messages</h2>
        <button
          className="filter-toggle"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter size={20} />
          Filters
        </button>
      </div>

      {/* Search Input */}
      <div className="search-input-wrapper">
        <Search className="search-icon" size={20} />
        <input
          type="text"
          className="search-input"
          placeholder="Search messages..."
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
              Channel
            </label>
            <input
              type="text"
              placeholder="Channel ID"
              value={filters.channel}
              onChange={(e) =>
                setFilters({ ...filters, channel: e.target.value })
              }
            />
          </div>

          <div className="filter-group">
            <label>
              <User size={16} />
              User
            </label>
            <input
              type="text"
              placeholder="User ID"
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
          Found {pagination.count} result{pagination.count !== 1 ? 's' : ''} for "
          <strong>{query}</strong>"
        </div>
      )}

      {/* Loading State */}
      {loading && results.length === 0 && (
        <div className="search-loading">
          <div className="loading-spinner"></div>
          <p>Searching...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="search-error">
          <p>Error: {error}</p>
          <button onClick={() => performSearch()}>Retry</button>
        </div>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && !error && (
        <div className="no-results">
          <Search size={48} />
          <p>No messages found for "{query}"</p>
          <p className="hint">Try different keywords or adjust filters</p>
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
                  <span className="username">{message.user?.username || 'Unknown'}</span>
                </div>

                <div className="message-meta">
                  <span className="channel-name">
                    <Hash size={14} />
                    {message.channel?.name || `Channel ${message.channel_id}`}
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
                  📎 Has attachment
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
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!query && results.length === 0 && (
        <div className="empty-state">
          <Search size={64} />
          <p>Enter a search query to find messages</p>
          <p className="hint">You can search across all your channels</p>
        </div>
      )}
    </div>
  );
};

export default ChatMessageSearch;
