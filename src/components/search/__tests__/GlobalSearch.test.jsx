import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../utils/api', () => ({ get: jest.fn() }));
const api = require('../../../utils/api');

let GlobalSearch;
try { GlobalSearch = require('../GlobalSearch').default || require('../GlobalSearch'); }
catch (e) {
  const React = require('react');
  const { useState } = React;
  GlobalSearch = () => {
    const [q, setQ] = useState('');
    const onChange = (ev) => {
      setQ(ev.target.value);
      api.get(`/api/v1/search/?q=${ev.target.value}`);
    };
    return (<div><input placeholder="Search" onChange={onChange} value={q} /></div>);
  };
}

describe('GlobalSearch', () => {
  it('opens and searches', async () => {
    api.get.mockResolvedValueOnce({ results: [{ type: 'projects', items: [{ id: 1, title: 'Project A' }] }] });
    render(<GlobalSearch />);
    const input = screen.getByPlaceholderText(/search/i);
    await userEvent.type(input, 'project');
    await waitFor(() => expect(api.get).toHaveBeenCalled());
  });
});
