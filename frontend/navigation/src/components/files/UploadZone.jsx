import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';
import './UploadZone.css';

const UploadZone = ({ onUpload, uploading, uploadProgress }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (onUpload) {
      onUpload(acceptedFiles);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 10485760 // 10MB
  });

  return (
    <div 
      {...getRootProps()} 
      className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
    >
      <input {...getInputProps()} />
      
      <div className="upload-zone-content">
        {uploading ? (
          <>
            <div className="upload-spinner"></div>
            <p className="upload-percentage">{uploadProgress}%</p>
            <div className="upload-progress-bar">
              <div 
                className="upload-progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </>
        ) : isDragActive ? (
          <>
            <Upload size={48} className="upload-icon pulse" />
            <p className="upload-text">Drop files here...</p>
          </>
        ) : (
          <>
            <Upload size={48} className="upload-icon" />
            <p className="upload-text">Drag & drop files here</p>
            <p className="upload-hint">or click to browse</p>
            <p className="upload-hint">Maximum file size: 10MB</p>
          </>
        )}
      </div>
    </div>
  );
};

export default UploadZone;
