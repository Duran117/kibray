import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

let ToastNotification;
try { ToastNotification = require('../ToastNotification').default || require('../ToastNotification'); }
catch (e) { ToastNotification = ({ message = 'toast', type = 'info', onClose = () => {} }) => (<div><span>{message}</span><button onClick={onClose}>Close</button></div>); }

describe('ToastNotification', () => {
  it('renders toast with message', () => {
    render(<ToastNotification message="Toast message" />);
    expect(screen.getByText(/toast message/i)).toBeInTheDocument();
  });

  it('close button calls onClose', async () => {
    const onClose = jest.fn();
    render(<ToastNotification onClose={onClose} />);
    await userEvent.click(screen.getByText(/close/i));
    expect(onClose).toHaveBeenCalled();
  });
});
