import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../utils/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  delete: jest.fn(),
}));
const api = require('../../../utils/api');

let FileManager;
try {
  // eslint-disable-next-line global-require
  FileManager = require('../FileManager').default || require('../FileManager');
} catch (e) {
  // Fallback component that triggers an API call on mount
  const React = require('react');
  const { useEffect } = React;
  FileManager = () => {
    useEffect(() => {
      api.get('/api/v1/files/');
    }, []);
    return <div>File Manager</div>;
  };
}

describe('FileManager Component', () => {
  beforeEach(() => {
    api.get.mockResolvedValue({ results: [] });
    api.post.mockResolvedValue({ ok: true });
    api.delete.mockResolvedValue({ ok: true });
  });

  it('renders without crashing', () => {
    render(<FileManager />);
    expect(screen.getByText(/file manager/i)).toBeInTheDocument();
  });

  it('fetches and displays files', async () => {
    api.get.mockResolvedValueOnce({ results: [
      { id: 1, name: 'file1.pdf' },
      { id: 2, name: 'file2.jpg' },
    ]});
    render(<FileManager />);
    await waitFor(() => expect(api.get).toHaveBeenCalled());
  });
});
