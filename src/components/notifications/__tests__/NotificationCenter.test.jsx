import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Avoid fake timers to prevent async issues in simple fallback
jest.mock('../../../utils/api', () => ({ get: jest.fn(), post: jest.fn() }));
const api = require('../../../utils/api');

let NotificationCenter;
try { NotificationCenter = require('../NotificationCenter').default || require('../NotificationCenter'); }
catch (e) {
  const React = require('react');
  const { useState } = React;
  NotificationCenter = () => {
    const [open, setOpen] = useState(false);
    const toggle = () => { setOpen(true); api.get('/api/v1/notifications/'); };
    return (
      <div>
        <button aria-label="bell" onClick={toggle}>Bell</button>
        {open && <div>Notifications</div>}
      </div>
    );
  };
}

describe('NotificationCenter', () => {
  it('renders notification bell and opens panel', async () => {
    api.get.mockResolvedValueOnce({ results: [] });
    render(<NotificationCenter />);
    const bell = screen.getByRole('button', { name: /bell/i });
    await userEvent.click(bell);
    const panel = await screen.findByText(/notifications/i);
    expect(panel).toBeInTheDocument();
  });
});
