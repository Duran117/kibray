import React from 'react';
import { useNavigation } from '../../context/NavigationContext.jsx';
import './Breadcrumbs.css';

const Breadcrumbs = () => {
  const { breadcrumbs, navigateToBreadcrumb } = useNavigation();
  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {breadcrumbs.map((bc, idx) => (
        <span key={idx} className="breadcrumb-item">
          <button
            className="breadcrumb-btn"
            disabled={idx === breadcrumbs.length - 1}
            onClick={() => navigateToBreadcrumb(idx)}
          >
            {bc.label}
          </button>
          {idx < breadcrumbs.length - 1 && <span className="breadcrumb-separator">/</span>}
        </span>
      ))}
    </nav>
  );
};

export default Breadcrumbs;
