import React from 'react';
import { FileText, CheckSquare, Folder, Building2 } from 'lucide-react';
import './SearchResults.css';

const SearchResults = ({ results, query }) => {
  if (!query) {
    return (
      <div className="search-empty">
        <p>Start typing to search...</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="search-empty">
        <p>No results found for "{query}"</p>
      </div>
    );
  }

  const groupedResults = results.reduce((acc, item) => {
    const type = item.type || 'other';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(item);
    return acc;
  }, {});

  const getIcon = (type) => {
    switch (type) {
      case 'project':
        return <Building2 size={20} />;
      case 'task':
        return <CheckSquare size={20} />;
      case 'file':
        return <FileText size={20} />;
      default:
        return <Folder size={20} />;
    }
  };

  const getTypeLabel = (type) => {
    return type.charAt(0).toUpperCase() + type.slice(1) + 's';
  };

  return (
    <div className="search-results">
      {Object.entries(groupedResults).map(([type, items]) => (
        <div key={type} className="result-group">
          <h4 className="result-group-title">{getTypeLabel(type)}</h4>
          {items.map(item => (
            <div key={item.id} className="result-item">
              <div className="result-icon">
                {getIcon(item.type)}
              </div>
              <div className="result-content">
                <h5>{item.title || item.name}</h5>
                <p>{item.description || item.address || ''}</p>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default SearchResults;
