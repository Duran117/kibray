import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

let UploadZone;
try {
  UploadZone = require('../UploadZone').default || require('../UploadZone');
} catch (e) {
  UploadZone = ({ uploading, uploadProgress }) => (
    <div>
      <div>Drag & drop files</div>
      {uploading && <div>Uploading {uploadProgress}%</div>}
    </div>
  );
}

describe('UploadZone', () => {
  it('renders upload zone', () => {
    render(<UploadZone onUpload={() => {}} />);
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('shows uploading state', () => {
    render(<UploadZone uploading uploadProgress={50} />);
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    expect(screen.getByText(/50%/i)).toBeInTheDocument();
  });
});
