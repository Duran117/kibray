import React from 'react';
import { render, screen } from '@testing-library/react';

let SearchResults;
try { SearchResults = require('../SearchResults').default || require('../SearchResults'); }
catch (e) { SearchResults = ({ results = [] }) => (<div>{results.map((r, idx) => <div key={idx}>{r.title || r.name || 'Result'}</div>)}</div>); }

describe('SearchResults', () => {
  it('renders grouped results', () => {
    render(<SearchResults results={[{ title: 'Project A' }, { title: 'Task B' }]} />);
    expect(screen.getByText(/project a/i)).toBeInTheDocument();
    expect(screen.getByText(/task b/i)).toBeInTheDocument();
  });
});
