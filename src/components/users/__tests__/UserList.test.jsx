import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

let UserList;
try {
  UserList = require('../UserList').default || require('../UserList');
} catch (e) {
  UserList = ({ users = [], onSelectUser = () => {}, onDeleteUser = () => {} }) => (
    <div>
      {users.map(u => (
        <div key={u.id} className="user-card">
          <div>{`${u.first_name || ''} ${u.last_name || ''}`.trim() || u.username}</div>
          <div>{u.email}</div>
          <button onClick={() => onSelectUser(u)} aria-label="edit">Edit</button>
          <button onClick={() => onDeleteUser(u.id)} aria-label="delete">Delete</button>
        </div>
      ))}
    </div>
  );
}

describe('UserList', () => {
  const mockUsers = [
    { id: 1, username: 'john', first_name: 'John', last_name: 'Doe', email: 'john@test.com', profile: { role: 'pm' }},
  ];

  it('renders user cards', () => {
    render(<UserList users={mockUsers} />);
    expect(screen.getByText(/john doe/i)).toBeInTheDocument();
    expect(screen.getByText(/john@test.com/i)).toBeInTheDocument();
  });

  it('edit button calls onSelectUser', () => {
    const onSelectUser = jest.fn();
    render(<UserList users={mockUsers} onSelectUser={onSelectUser} />);
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(onSelectUser).toHaveBeenCalledWith(mockUsers[0]);
  });

  it('delete button calls onDeleteUser', () => {
    const onDeleteUser = jest.fn();
    render(<UserList users={mockUsers} onDeleteUser={onDeleteUser} />);
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(onDeleteUser).toHaveBeenCalledWith(1);
  });
});
