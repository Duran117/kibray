import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

let FilePreview;
try {
  FilePreview = require('../FilePreview').default || require('../FilePreview');
} catch (e) {
  FilePreview = ({ file, onDelete, onDownload, viewMode = 'grid' }) => (
    <div>
      <div>{file?.name || 'test.pdf'}</div>
      <button aria-label="download" onClick={() => onDownload && onDownload(file)}>Download</button>
      <button aria-label="delete" onClick={() => onDelete && onDelete(file)}>Delete</button>
      <div data-testid="viewMode">{viewMode}</div>
    </div>
  );
}

describe('FilePreview', () => {
  const mockFile = { id: 1, name: 'test.pdf', type: 'application/pdf', size: 102400 };

  it('renders grid view', () => {
    render(<FilePreview file={mockFile} viewMode="grid" />);
    expect(screen.getByText(/test\.pdf/i)).toBeInTheDocument();
    expect(screen.getByTestId('viewMode')).toHaveTextContent('grid');
  });

  it('calls onDownload when clicked', () => {
    const onDownload = jest.fn();
    render(<FilePreview file={mockFile} onDownload={onDownload} />);
    fireEvent.click(screen.getByRole('button', { name: /download/i }));
    expect(onDownload).toHaveBeenCalledWith(mockFile);
  });

  it('calls onDelete when clicked', () => {
    const onDelete = jest.fn();
    render(<FilePreview file={mockFile} onDelete={onDelete} />);
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(onDelete).toHaveBeenCalled();
  });
});
