import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Image, File, Download, Trash2 } from 'lucide-react';
import './FilePreview.css';

const FilePreview = ({ file, viewMode, onDelete, onDownload, formatSize, formatDate }) => {
  const { t } = useTranslation();
  const getFileIcon = (type) => {
    if (type?.startsWith('image/')) return <Image size={24} />;
    if (type === 'application/pdf') return <FileText size={24} />;
    return <File size={24} />;
  };

  const getFileThumb = () => {
    if (file.type?.startsWith('image/')) {
      return <img src={file.file_url} alt={file.name} className="file-thumb-img" />;
    }
    return <div className="file-thumb-icon">{getFileIcon(file.type)}</div>;
  };

  if (viewMode === 'list') {
    return (
      <div className="file-item-list">
        <div className="file-list-thumb">
          {getFileThumb()}
        </div>
        
        <div className="file-list-info">
          <h4 className="file-list-name">{file.name}</h4>
          <div className="file-list-meta">
            <span>{formatSize(file.size)}</span>
            <span className="bullet">•</span>
            <span>{file.category}</span>
            <span className="bullet">•</span>
            <span>{t('files.by_user', { user: (file.uploaded_by?.username || file.uploaded_by || t('common.unknown', { defaultValue: 'Unknown' })), defaultValue: 'by {{user}}' })}</span>
            <span className="bullet">•</span>
            <span>{formatDate(file.uploaded_at)}</span>
          </div>
        </div>
        
        <div className="file-list-actions">
          <button 
            className="file-action-btn download"
            onClick={onDownload}
            title={t('files.download')}
          >
            <Download size={18} />
          </button>
          <button 
            className="file-action-btn delete"
            onClick={onDelete}
            title={t('common.delete')}
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="file-item-grid">
      <div className="file-grid-thumb">
        {getFileThumb()}
      </div>
      
      <div className="file-grid-info">
        <h4 className="file-grid-name" title={file.name}>{file.name}</h4>
        <div className="file-grid-meta">
          <span>{formatSize(file.size)}</span>
          <span>{formatDate(file.uploaded_at)}</span>
        </div>
        <div className="file-grid-footer">
          <span>{file.uploaded_by?.username || t('common.unknown', { defaultValue: 'Unknown' })}</span>
        </div>
      </div>
      
      <div className="file-grid-actions">
        <button 
          className="file-action-btn download"
          onClick={onDownload}
          title={t('files.download')}
        >
          <Download size={16} />
        </button>
        <button 
          className="file-action-btn delete"
          onClick={onDelete}
          title={t('common.delete')}
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  );
};

export default FilePreview;
