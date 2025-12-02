import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText } from 'lucide-react';
import './ReportTemplates.css';

const ReportTemplates = ({ templates, onSelect, selected }) => {
  const { t } = useTranslation();
  return (
    <div className="report-templates">
      <h3>{t('reports.select_template')}</h3>
      <div className="template-grid">
        {templates.map(template => (
          <div 
            key={template}
            className={`template-card ${selected === template ? 'selected' : ''}`}
            onClick={() => onSelect(template)}
          >
            <FileText size={32} />
            <h4>{template}</h4>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReportTemplates;
