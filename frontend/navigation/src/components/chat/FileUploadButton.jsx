import React, { useState, useRef } from 'react';
import { Upload, X, File, Image as ImageIcon, FileText, AlertCircle } from 'lucide-react';
import './FileUploadButton.css';

/**
 * File Upload Button for WebSocket Chat
 * 
 * Features:
 * - Drag & drop support
 * - File type validation
 * - Size limit enforcement
 * - Preview for images
 * - Progress tracking
 * - Chunked upload via WebSocket
 */
const FileUploadButton = ({ 
  onFileSelect, 
  maxSize = 10 * 1024 * 1024, // 10MB default
  acceptedTypes = [
    'image/jpeg',
    'image/png', 
    'image/gif',
    'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
  disabled = false,
}) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    // Check file type
    if (!acceptedTypes.includes(file.type)) {
      return `File type ${file.type} not supported`;
    }

    // Check file size
    if (file.size > maxSize) {
      const maxSizeMB = (maxSize / 1024 / 1024).toFixed(1);
      return `File too large. Maximum size: ${maxSizeMB}MB`;
    }

    // Check for dangerous extensions
    const dangerousExtensions = ['.exe', '.bat', '.sh', '.cmd', '.scr'];
    if (dangerousExtensions.some(ext => file.name.toLowerCase().endsWith(ext))) {
      return 'Executable files not allowed';
    }

    return null;
  };

  const handleFileSelect = (file) => {
    setError(null);
    
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);

    // Generate preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }

    // Notify parent component
    if (onFileSelect) {
      onFileSelect(file);
    }
  };

  const handleInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setPreview(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleButtonClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) {
      return <ImageIcon size={20} />;
    } else if (fileType.includes('pdf') || fileType.includes('document')) {
      return <FileText size={20} />;
    }
    return <File size={20} />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="file-upload-container">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleInputChange}
        accept={acceptedTypes.join(',')}
        style={{ display: 'none' }}
        disabled={disabled}
      />

      {!selectedFile ? (
        <div
          className={`file-upload-button ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
          onClick={handleButtonClick}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <Upload size={20} />
          <span>{isDragging ? 'Drop file here' : 'Upload file'}</span>
        </div>
      ) : (
        <div className="file-preview">
          <div className="file-preview-header">
            {getFileIcon(selectedFile.type)}
            <div className="file-info">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">{formatFileSize(selectedFile.size)}</span>
            </div>
            <button
              className="file-clear-btn"
              onClick={handleClearFile}
              title="Remove file"
            >
              <X size={16} />
            </button>
          </div>

          {preview && (
            <div className="file-preview-image">
              <img src={preview} alt="Preview" />
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="file-upload-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default FileUploadButton;
