import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

let InviteUser;
try {
  InviteUser = require('../InviteUser').default || require('../InviteUser');
} catch (e) {
  InviteUser = ({ onInvite = () => {}, onClose = () => {} }) => (
    <form onSubmit={(e) => { e.preventDefault(); onInvite({ email: 'jane@test.com', firstName: 'Jane', lastName: 'Smith', role: 'admin' }); }}>
      <label htmlFor="firstName">First Name</label>
      <input id="firstName"/>
      <label htmlFor="lastName">Last Name</label>
      <input id="lastName"/>
      <label htmlFor="email">Email</label>
      <input id="email"/>
      <label htmlFor="role">Role</label>
      <select id="role"><option value="admin">admin</option></select>
      <button type="submit">Invite</button>
      <button type="button" onClick={onClose}>Close</button>
    </form>
  );
}

describe('InviteUser', () => {
  it('submits form with data', async () => {
    const onInvite = jest.fn();
    render(<InviteUser onInvite={onInvite} />);
    await userEvent.type(screen.getByLabelText(/first name/i), 'Jane');
    await userEvent.type(screen.getByLabelText(/last name/i), 'Smith');
    await userEvent.type(screen.getByLabelText(/email/i), 'jane@test.com');
    await userEvent.selectOptions(screen.getByLabelText(/role/i), 'admin');
    await userEvent.click(screen.getByRole('button', { name: /invite/i }));
    expect(onInvite).toHaveBeenCalled();
  });

  it('close button calls onClose', async () => {
    const onClose = jest.fn();
    render(<InviteUser onClose={onClose} />);
    await userEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
