import React, { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useDropzone } from 'react-dropzone';
import { Upload, File } from 'lucide-react';
import './UploadZone.css';

const UploadZone = ({ onUpload, uploading, uploadProgress }) => {
  const { t } = useTranslation();
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
            <p className="upload-text">{t('files.drop_here', { defaultValue: 'Drop files here...' })}</p>
          </>
        ) : (
          <>
            <Upload size={48} className="upload-icon" />
            <p className="upload-text">{t('files.drag_and_drop_here', { defaultValue: 'Drag & drop files here' })}</p>
            <p className="upload-hint">{t('files.click_to_browse', { defaultValue: 'or click to browse' })}</p>
            <p className="upload-hint">{t('files.max_file_size', { size: '10MB', defaultValue: 'Maximum file size: {{size}}' })}</p>
          </>
        )}
      </div>
    </div>
  );
};

export default UploadZone;
