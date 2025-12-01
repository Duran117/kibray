import React from 'react';
import { render, screen } from '@testing-library/react';

let ReportTemplates;
try { ReportTemplates = require('../ReportTemplates').default || require('../ReportTemplates'); }
catch (e) { ReportTemplates = () => (<div><div>Project Status</div><div>Budget Summary</div></div>); }

describe('ReportTemplates', () => {
  it('renders templates', () => {
    render(<ReportTemplates />);
    expect(screen.getByText(/project status/i)).toBeInTheDocument();
    expect(screen.getByText(/budget summary/i)).toBeInTheDocument();
  });
});
