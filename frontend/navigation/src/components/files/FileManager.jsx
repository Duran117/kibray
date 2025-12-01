import React, { useState, useEffect } from 'react';
import { useNavigation } from '../../context/NavigationContext';
import UploadZone from './UploadZone';
import FilePreview from './FilePreview';
import api from '../../utils/api';
import { Folder, Grid, List, Search, Upload, Download, Trash2 } from 'lucide-react';
import { useFileUpload } from '../../hooks/useFileUpload';
import './FileManager.css';

const FileManager = () => {
  const { currentContext } = useNavigation();
  const [files, setFiles] = useState([]);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { uploadFiles, uploading, uploadProgress } = useFileUpload();

  useEffect(() => {
    fetchFiles();
  }, [currentContext.projectId, selectedCategory]);

  const fetchFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const projectParam = currentContext.projectId ? `&project=${currentContext.projectId}` : '';
      const categoryParam = selectedCategory !== 'all' ? `&category=${selectedCategory}` : '';
      const data = await api.get(`/files/?ordering=-uploaded_at${projectParam}${categoryParam}`);
      setFiles(data.results || data);
    } catch (err) {
      console.error('Failed to fetch files:', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (uploadedFiles) => {
    try {
      const formData = new FormData();
      uploadedFiles.forEach(file => {
        formData.append('files', file);
      });
      
      if (currentContext.projectId) {
        formData.append('project', currentContext.projectId);
      }
      formData.append('category', selectedCategory !== 'all' ? selectedCategory : 'documents');
      
      await api.post('/files/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      fetchFiles(); // Refresh list
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed. Please try again.');
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
      await api.delete(`/files/${fileId}/`);
      setFiles(prev => prev.filter(f => f.id !== fileId));
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Delete failed. Please try again.');
    }
  };

  const handleDownload = async (file) => {
    try {
      const response = await fetch(file.file_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Download failed. Please try again.');
    }
  };

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="file-manager">
      <div className="file-manager-header">
        <div className="file-manager-title-section">
          <Folder size={28} />
          <h1>File Manager</h1>
        </div>
        
        <div className="file-manager-controls">
          <div className="search-box">
            <Search size={18} />
            <input 
              type="text" 
              placeholder="Search files..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <select 
            className="category-filter" 
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            <option value="drawings">Drawings</option>
            <option value="photos">Photos</option>
            <option value="invoices">Invoices</option>
            <option value="change-orders">Change Orders</option>
            <option value="contracts">Contracts</option>
            <option value="reports">Reports</option>
          </select>
          
          <div className="view-toggle">
            <button 
              className={viewMode === 'grid' ? 'active' : ''}
              onClick={() => setViewMode('grid')}
            >
              <Grid size={18} />
            </button>
            <button 
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              <List size={18} />
            </button>
          </div>
        </div>
      </div>

      <UploadZone 
        onUpload={handleUpload} 
        uploading={uploading}
        uploadProgress={uploadProgress}
      />

      {loading ? (
        <div className="files-loading">
          <div className="spinner"></div>
          <p>Loading files...</p>
        </div>
      ) : error ? (
        <div className="files-error">
          <p>{error}</p>
          <button onClick={fetchFiles}>Retry</button>
        </div>
      ) : (
        <div className={`files-${viewMode}`}>
          {filteredFiles.length > 0 ? (
            filteredFiles.map(file => (
              <FilePreview
                key={file.id}
                file={file}
                viewMode={viewMode}
                onDelete={() => handleDelete(file.id)}
                onDownload={() => handleDownload(file)}
                formatSize={formatFileSize}
                formatDate={formatDate}
              />
            ))
          ) : (
            <div className="no-files">
              <Folder size={48} />
              <p>No files found</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileManager;
