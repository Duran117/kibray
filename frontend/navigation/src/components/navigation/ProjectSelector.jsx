
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '../../context/NavigationContext';
import { ChevronDown, Search, Building2, MapPin, Check } from 'lucide-react';
import { api, MOCK_MODE, mockApi } from '../../utils/api';
import './ProjectSelector.css';

const ProjectSelector = () => {
  const { t } = useTranslation();
  const { currentContext, updateContext, pushBreadcrumb } = useNavigation();
  const [isOpen, setIsOpen] = useState(false);
  const [projects, setProjects] = useState([]);
  const [filteredProjects, setFilteredProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    if (isOpen && projects.length === 0) {
      fetchProjects();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = projects.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.billing_organization?.name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredProjects(filtered);
    } else {
      setFilteredProjects(projects);
    }
  }, [searchTerm, projects]);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = MOCK_MODE ? mockApi.projects : await api.get('/projects/assigned/');
      setProjects(data);
      setFilteredProjects(data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setProjects(mockApi.projects);
      setFilteredProjects(mockApi.projects);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project) => {
    updateContext({
      projectId: project.id,
      projectName: project.name,
      projectAddress: project.address,
      billingOrganization: project.billing_organization
    });
    pushBreadcrumb({ label: project.name, route: `/projects/${project.id}` });
    setIsOpen(false);
    setSearchTerm('');
  };

  const toggleDropdown = () => setIsOpen(!isOpen);

  return (
    <div className="project-selector" ref={dropdownRef}>
      <button className="project-selector-trigger" onClick={toggleDropdown}>
        <div className="project-selector-content">
          {currentContext.projectName ?  (
            <>
              <Building2 size={18} />
              <div className="project-info">
                <span className="project-name">{currentContext.projectName}</span>
                {currentContext.projectAddress && (
                  <span className="project-address">{currentContext.projectAddress}</span>
                )}
              </div>
            </>
          ) : (
            <>
              <Building2 size={18} />
              <span className="project-placeholder">{t('navigation.current_project')}</span>
            </>
          )}
        </div>
        <ChevronDown size={18} className={`chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div className="project-dropdown">
          <div className="project-search">
            <Search size={16} />
            <input
              type="text"
              className="search-input"
              placeholder={`${t('search.placeholder')} ${t('navigation.projects') || 'projects'}...`}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
          </div>

          <div className="project-list">
            {loading ? (
              <div className="project-loading">{t('common.loading')}</div>
            ) : filteredProjects.length > 0 ? (
              filteredProjects.map((project) => (
                <button
                  key={project.id}
                  className={`project-item ${currentContext.projectId === project.id ? 'active' : ''}`}
                  onClick={() => handleSelectProject(project)}
                >
                  <div className="project-item-header">
                    <span className="project-item-name">{project.name}</span>
                    {currentContext.projectId === project.id && (
                      <Check size={16} className="check-icon" />
                    )}
                  </div>
                  {project.billing_organization && (
                    <div className="project-organization">
                      <Building2 size={14} />
                      <span>{project.billing_organization.name}</span>
                    </div>
                  )}
                  {project.address && (
                    <div className="project-location">
                      <MapPin size={14} />
                      <span>{project.address}</span>
                    </div>
                  )}
                </button>
              ))
            ) : (
              <div className="no-projects">{t('search.no_results')}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectSelector;
