// useFileUpload Hook - Manages file upload state and logic
import { useState } from 'react';
import { fileService } from '../services/fileService';

export const useFileUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  /**
   * Upload files
   * @param {File[]} files - Files to upload
   * @param {string} projectId - Project ID
   * @returns {Promise<Object[]>} Uploaded files metadata
   */
  const uploadFiles = async (files, projectId) => {
    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Validate files
      const validationErrors = [];
      files.forEach(file => {
        const validation = fileService.validateFile(file, {
          maxSize: 10 * 1024 * 1024, // 10MB
          allowedTypes: ['image/*', 'application/pdf', 'application/vnd.ms-excel'],
          allowedExtensions: ['jpg', 'jpeg', 'png', 'pdf', 'xlsx', 'xls', 'doc', 'docx']
        });

        if (!validation.valid) {
          validationErrors.push({
            file: file.name,
            errors: validation.errors
          });
        }
      });

      if (validationErrors.length > 0) {
        throw new Error(`Validation failed: ${JSON.stringify(validationErrors)}`);
      }

      // Upload files
      const uploadedFiles = await fileService.uploadFiles(
        files,
        projectId,
        (progress) => {
          setUploadProgress(progress);
        }
      );

      setUploadProgress(100);
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 500);

      return uploadedFiles;
    } catch (err) {
      setError(err.message);
      setUploading(false);
      setUploadProgress(0);
      throw err;
    }
  };

  /**
   * Reset upload state
   */
  const reset = () => {
    setUploading(false);
    setUploadProgress(0);
    setError(null);
  };

  return {
    uploading,
    uploadProgress,
    error,
    uploadFiles,
    reset
  };
};

export default useFileUpload;
