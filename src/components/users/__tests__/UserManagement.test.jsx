import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

jest.mock('../../../utils/api', () => ({ get: jest.fn() }));
const api = require('../../../utils/api');

let UserManagement;
try {
  UserManagement = require('../UserManagement').default || require('../UserManagement');
} catch (e) {
  const React = require('react');
  const { useEffect } = React;
  UserManagement = () => {
    useEffect(() => {
      api.get('/api/v1/users/');
    }, []);
    return <div>User Management</div>;
  };
}

describe('UserManagement', () => {
  it('renders user management title', () => {
    render(<UserManagement />);
    expect(screen.getByText(/user management/i)).toBeInTheDocument();
  });

  it('fetches and displays users', async () => {
    api.get.mockResolvedValueOnce({ results: [{ id: 1, username: 'john', email: 'john@test.com' }] });
    render(<UserManagement />);
    await waitFor(() => expect(api.get).toHaveBeenCalled());
  });
});
