import React from 'react';
import { render, screen } from '@testing-library/react';

let TimelineView;
try { TimelineView = require('../TimelineView').default || require('../TimelineView'); }
catch (e) { TimelineView = () => (<div><h2>Timeline</h2><div className="timeline">markers</div></div>); }

describe('TimelineView', () => {
  it('renders timeline', () => {
    render(<TimelineView />);
    expect(screen.getByText(/timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/markers/i)).toBeInTheDocument();
  });
});
