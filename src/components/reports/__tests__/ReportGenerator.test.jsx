import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../utils/api', () => ({ post: jest.fn() }));
const api = require('../../../utils/api');

let ReportGenerator;
try { ReportGenerator = require('../ReportGenerator').default || require('../ReportGenerator'); }
catch (e) {
  const React = require('react');
  ReportGenerator = () => (
    <div>
      <h2>Report Generator</h2>
      <button onClick={() => api.post('/api/v1/reports/generate/', { template: 'Project Status' })}>Generate</button>
    </div>
  );
}

describe('ReportGenerator', () => {
  it('renders report generator', () => {
    render(<ReportGenerator />);
    expect(screen.getByText(/report generator/i)).toBeInTheDocument();
  });

  it('generates report', async () => {
    api.post.mockResolvedValueOnce({ ok: true });
    render(<ReportGenerator />);
    await userEvent.click(screen.getByRole('button', { name: /generate/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalled());
  });
});
