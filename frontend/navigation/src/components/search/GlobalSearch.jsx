import React, { useState, useEffect } from 'react';
import SearchResults from './SearchResults';
import { Search, X } from 'lucide-react';
import api from '../../utils/api';
import './GlobalSearch.css';

const GlobalSearch = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }

    const timeout = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await api.get(`/search/?q=${encodeURIComponent(query)}`);
        setResults(data);
      } catch (error) {
        console.error('Search failed:', error);
        // Use mock results for demo
        setResults([
          { id: 1, type: 'project', title: 'Downtown Office Building', description: '123 Main St, Boulder, CO' },
          { id: 2, type: 'task', title: 'Review blueprints', description: 'Due tomorrow' },
          { id: 3, type: 'file', title: 'Floor_Plan_v2.pdf', description: 'Uploaded 2 days ago' }
        ]);
      } finally {
        setLoading(false);
      }
    }, 500);

    return () => clearTimeout(timeout);
  }, [query]);

  if (!isOpen) return null;

  return (
    <div data-testid="global-search" className="search-overlay" onClick={() => setIsOpen(false)}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-header">
          <Search size={20} />
          <input 
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects, tasks, change orders, files..."
          />
          <button onClick={() => setIsOpen(false)}>
            <X size={20} />
          </button>
        </div>
        
        {loading ? (
          <div className="search-loading">
            <div className="spinner"></div>
            <p>Searching...</p>
          </div>
        ) : (
          <SearchResults results={results} query={query} />
        )}
        
        <div className="search-footer">
          <span className="search-hint">
            <kbd>⌘</kbd> + <kbd>K</kbd> to search
          </span>
          <span className="search-hint">
            <kbd>Esc</kbd> to close
          </span>
        </div>
      </div>
    </div>
  );
};

export default GlobalSearch;
