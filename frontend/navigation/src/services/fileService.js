// File Service - Handles file uploads, downloads, and management
import { api } from '../utils/api';

export const fileService = {
  /**
   * Upload files to the server
   * @param {File[]} files - Array of File objects
   * @param {string} projectId - Project ID for file association
   * @param {Function} onProgress - Progress callback (percent)
   * @returns {Promise<Object[]>} Uploaded file metadata
   */
  async uploadFiles(files, projectId, onProgress) {
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file);
    });
    
    if (projectId) {
      formData.append('projectId', projectId);
    }

    try {
      const response = await fetch('/api/v1/files/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include',
        headers: {
          'X-CSRFToken': this.getCsrfToken()
        },
        // Track upload progress
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          if (onProgress) onProgress(percent);
        }
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('File upload error:', error);
      throw error;
    }
  },

  /**
   * Download a file
   * @param {string} fileUrl - File URL or ID
   * @returns {Promise<Blob>} File blob
   */
  async downloadFile(fileUrl) {
    try {
      const response = await fetch(fileUrl, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('File download error:', error);
      throw error;
    }
  },

  /**
   * Delete a file
   * @param {number} fileId - File ID
   * @returns {Promise<void>}
   */
  async deleteFile(fileId) {
    return await api.delete(`/files/${fileId}`);
  },

  /**
   * Get files list
   * @param {string} projectId - Project ID (or 'all')
   * @param {Object} filters - Filter options
   * @returns {Promise<Object[]>} Files array
   */
  async getFiles(projectId = 'all', filters = {}) {
    const queryParams = new URLSearchParams(filters).toString();
    return await api.get(`/files/${projectId}?${queryParams}`);
  },

  /**
   * Validate file before upload
   * @param {File} file - File to validate
   * @param {Object} options - Validation options
   * @returns {Object} Validation result
   */
  validateFile(file, options = {}) {
    const {
      maxSize = 10 * 1024 * 1024, // 10MB default
      allowedTypes = [],
      allowedExtensions = []
    } = options;

    const errors = [];

    // Check file size
    if (file.size > maxSize) {
      errors.push(`File size exceeds ${this.formatBytes(maxSize)}`);
    }

    // Check file type
    if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
      errors.push(`File type ${file.type} not allowed`);
    }

    // Check file extension
    if (allowedExtensions.length > 0) {
      const extension = file.name.split('.').pop().toLowerCase();
      if (!allowedExtensions.includes(extension)) {
        errors.push(`File extension .${extension} not allowed`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  },

  /**
   * Format bytes to human-readable string
   * @param {number} bytes - Bytes
   * @param {number} decimals - Decimal places
   * @returns {string} Formatted string
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  },

  /**
   * Get file icon based on type
   * @param {string} mimeType - MIME type
   * @returns {string} Icon name
   */
  getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType === 'application/pdf') return 'pdf';
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return 'spreadsheet';
    if (mimeType.includes('document') || mimeType.includes('word')) return 'document';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return 'archive';
    return 'file';
  },

  /**
   * Get CSRF token from cookie or meta tag
   * @returns {string} CSRF token
   */
  getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  }
};

export default fileService;
