
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigation } from '../../context/NavigationContext';
import { ChevronRight, Home } from 'lucide-react';
import './Breadcrumbs.css';

const Breadcrumbs = () => {
  const { t } = useTranslation();
  const { breadcrumbs, navigateToBreadcrumb } = useNavigation();
  if (!breadcrumbs || breadcrumbs.length === 0) return null;

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      <ol className="breadcrumb-list">
        <li className="breadcrumb-item">
          <a href="/" className="breadcrumb-link" aria-label={t('navigation.dashboard')}>
            <Home size={16} />
            <span>{t('navigation.dashboard')}</span>
          </a>
        </li>
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          return (
            <React.Fragment key={`breadcrumb-${index}`}>
              <li className="breadcrumb-separator">
                <ChevronRight size={14} />
              </li>
              <li className={`breadcrumb-item ${isLast ? 'active' : ''}`}>
                {isLast ? (
                  <span className="breadcrumb-current">{crumb.label}</span>
                ) : (
                  <button
                    className="breadcrumb-link"
                    onClick={() => navigateToBreadcrumb(index)}
                  >
                    {crumb.label}
                  </button>
                )}
              </li>
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumbs;
