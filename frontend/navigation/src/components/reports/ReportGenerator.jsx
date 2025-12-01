import React, { useState } from 'react';
import ReportTemplates from './ReportTemplates';
import { FileText, Download } from 'lucide-react';
import api from '../../utils/api';
import './ReportGenerator.css';

const ReportGenerator = () => {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [generating, setGenerating] = useState(false);

  const templates = [
    'Project Status',
    'Weekly Progress',
    'Budget Summary',
    'Time Tracking',
    'Change Orders',
    'Team Performance'
  ];

  const handleGenerate = async () => {
    if (!selectedTemplate) {
      alert('Please select a template');
      return;
    }

    try {
      setGenerating(true);
      
      const data = await api.post('/reports/generate/', {
        template: selectedTemplate,
        dateRange
      });
      
      // Create blob and download
      const blob = new Blob([data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTemplate.toLowerCase().replace(/\s+/g, '-')}-report.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Report generation failed:', error);
      alert('Report generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="report-generator">
      <div className="report-header">
        <FileText size={28} />
        <h1>Report Generator</h1>
      </div>

      <ReportTemplates 
        templates={templates}
        onSelect={setSelectedTemplate}
        selected={selectedTemplate}
      />

      <div className="date-range">
        <label>
          From
          <input 
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
          />
        </label>
        <label>
          To
          <input 
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
          />
        </label>
      </div>

      <button 
        onClick={handleGenerate}
        disabled={!selectedTemplate || generating}
        className="generate-btn"
      >
        <Download size={18} />
        {generating ? 'Generating...' : 'Generate Report'}
      </button>
    </div>
  );
};

export default ReportGenerator;
