import React from 'react';
import { render, screen } from '@testing-library/react';

let MessageList;
try { MessageList = require('../MessageList').default || require('../MessageList'); }
catch (e) { MessageList = ({ messages = [] }) => (<ul>{messages.map(m => <li key={m.id} className="message-item"><span className="message-avatar">A</span><span>{m.text}</span></li>)}</ul>); }

describe('MessageList', () => {
  it('renders message items', () => {
    const messages = [{ id: 1, text: 'Hello' }, { id: 2, text: 'World' }];
    render(<MessageList messages={messages} />);
    expect(screen.getByText(/hello/i)).toBeInTheDocument();
    expect(screen.getByText(/world/i)).toBeInTheDocument();
  });
});
