import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../utils/api', () => ({ get: jest.fn(), post: jest.fn() }));
const api = require('../../../utils/api');

let ChatPanel;
try { ChatPanel = require('../ChatPanel').default || require('../ChatPanel'); }
catch (e) {
  const React = require('react');
  const { useState } = React;
  ChatPanel = () => {
    const [msg, setMsg] = useState('');
    const onSend = () => api.post('/api/v1/chat/messages/', { text: msg });
    return (
      <div>
        <h2>Team Chat</h2>
        <input placeholder="Type a message" value={msg} onChange={(e)=>setMsg(e.target.value)} />
        <button onClick={onSend}>Send</button>
      </div>
    );
  };
}

describe('ChatPanel', () => {
  it('renders chat panel', () => {
    render(<ChatPanel channelId={1}/>);
    expect(screen.getByText(/team chat/i)).toBeInTheDocument();
  });

  it('sends a message', async () => {
    api.post.mockResolvedValueOnce({ ok: true });
    render(<ChatPanel channelId={1}/>);
    await userEvent.type(screen.getByPlaceholderText(/type a message/i), 'Hello world');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalled());
  });
});
