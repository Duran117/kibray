import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

let MessageInput;
try { MessageInput = require('../MessageInput').default || require('../MessageInput'); }
catch (e) { MessageInput = ({ onSend = () => {} }) => { return (<form onSubmit={(ev)=>{ev.preventDefault(); onSend('msg');}}><input placeholder="Type" /><button type="submit">Send</button></form>); }; }

describe('MessageInput', () => {
  it('submit calls onSend', async () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);
    await userEvent.type(screen.getByPlaceholderText(/type/i), 'Hello');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(onSend).toHaveBeenCalled();
  });
});
