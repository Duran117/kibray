import React, { useEffect, useState } from 'react';
import { useNavigation } from '../../context/NavigationContext.jsx';
import { fetchAssignedProjects } from './api.js';
import './ProjectSelector.css';

const ProjectSelector = () => {
  const { currentContext, updateContext, pushBreadcrumb } = useNavigation();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchAssignedProjects().then(data => {
      setProjects(data);
    }).finally(() => setLoading(false));
  }, []);

  const handleSelect = (e) => {
    const projectId = e.target.value || null;
    const project = projects.find(p => p.id.toString() === projectId);
    updateContext({ projectId, projectName: project ? project.name : null });
    if (project) pushBreadcrumb(project.name, `/projects/${project.id}`);
  };

  return (
    <div className="project-selector">
      <label htmlFor="project-select">Project:</label>
      <select id="project-select" value={currentContext.projectId || ''} onChange={handleSelect} disabled={loading}>
        <option value="">All Projects</option>
        {projects.map(p => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      {loading && <span className="loading">Loading...</span>}
    </div>
  );
};

export default ProjectSelector;
