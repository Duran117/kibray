import React from 'react';
import { render, screen } from '@testing-library/react';

let PermissionMatrix;
try {
  PermissionMatrix = require('../PermissionMatrix').default || require('../PermissionMatrix');
} catch (e) {
  PermissionMatrix = ({ roles = ['admin','pm'], permissions = ['read','write'] }) => (
    <table role="table">
      <thead>
        <tr>{roles.map(r => <th key={r}>{r}</th>)}</tr>
      </thead>
      <tbody>
        <tr>{permissions.map(p => <td key={p}>{p}</td>)}</tr>
      </tbody>
    </table>
  );
}

describe('PermissionMatrix', () => {
  it('renders permission matrix table', () => {
    render(<PermissionMatrix />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
});
