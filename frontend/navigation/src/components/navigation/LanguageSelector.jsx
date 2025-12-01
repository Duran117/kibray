import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageSelector.css';

const LANG_OPTIONS = [
  { code: 'en', label: 'EN', name: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'ES', name: 'Español', flag: '🇲🇽' }
];

const LanguageSelector = ({ compact = false }) => {
  const { i18n, t } = useTranslation();
  const [open, setOpen] = useState(false);
  const current = LANG_OPTIONS.find(l => l.code === i18n.language) || LANG_OPTIONS[0];

  const changeLanguage = async (lng) => {
    await i18n.changeLanguage(lng);
    try {
      window.localStorage.setItem('i18nextLng', lng);
    } catch {}
    // Persist preference to backend if logged in
    try {
      const token = localStorage.getItem('authToken') || localStorage.getItem('kibray_access_token');
      if (token) {
        await fetch('/api/v1/users/preferred_language/', {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ preferred_language: lng })
        });
      }
    } catch (e) {
      // non-blocking
    }
    setOpen(false);
  };

  // Close on outside click
  useEffect(() => {
    const onClick = (e) => {
      if (!e.target.closest('.lang-selector')) setOpen(false);
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, []);

  if (compact) {
    return (
      <button
        className="lang-selector compact"
        aria-label={t('profile.language')}
        onClick={() => setOpen(!open)}
      >
        <span className="flag" aria-hidden>{current.flag}</span>
        <span className="code">{current.label}</span>
        {open && (
          <div className="lang-menu">
            {LANG_OPTIONS.map(opt => (
              <button
                key={opt.code}
                className={`lang-option ${opt.code === current.code ? 'active' : ''}`}
                onClick={() => changeLanguage(opt.code)}
              >
                <span className="flag" aria-hidden>{opt.flag}</span>
                <span className="name">{opt.name}</span>
              </button>
            ))}
          </div>
        )}
      </button>
    );
  }

  return (
    <div className="lang-selector" role="group" aria-label={t('profile.language')}>
      {LANG_OPTIONS.map(opt => (
        <button
          key={opt.code}
          className={`lang-btn ${opt.code === current.code ? 'active' : ''}`}
          onClick={() => changeLanguage(opt.code)}
          title={opt.name}
          aria-pressed={opt.code === current.code}
        >
          <span className="flag" aria-hidden>{opt.flag}</span>
          <span className="label">{opt.label}</span>
        </button>
      ))}
    </div>
  );
};

export default LanguageSelector;
