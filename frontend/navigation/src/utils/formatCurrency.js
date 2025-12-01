import i18n from '../i18n';

export const formatCurrency = (amount, { currency = 'USD' } = {}) => {
  try {
    const lng = i18n?.language || 'en';
    const locale = lng.startsWith('es') ? 'es-MX' : 'en-US';
    // If Mexican Spanish, prefer MXN by default
    const cur = currency || (locale === 'es-MX' ? 'MXN' : 'USD');
    return new Intl.NumberFormat(locale, { style: 'currency', currency: cur }).format(amount ?? 0);
  } catch (e) {
    return String(amount);
  }
};

export const formatNumber = (value, { maximumFractionDigits = 2 } = {}) => {
  try {
    const lng = i18n?.language || 'en';
    const locale = lng.startsWith('es') ? 'es-MX' : 'en-US';
    return new Intl.NumberFormat(locale, { maximumFractionDigits }).format(value ?? 0);
  } catch (e) {
    return String(value);
  }
};

export default formatCurrency;
