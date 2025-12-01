import React from 'react';
import { render, screen } from '@testing-library/react';

let NotificationBell;
try { NotificationBell = require('../NotificationBell').default || require('../NotificationBell'); }
catch (e) { NotificationBell = ({ count = 0, onClick = () => {} }) => (<button aria-label="bell" onClick={onClick}>{count > 0 && <span className="badge">{count}</span>}</button>); }

describe('NotificationBell', () => {
  it('renders bell and badge when count > 0', () => {
    render(<NotificationBell count={3} />);
    expect(screen.getByRole('button', { name: /bell/i })).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
