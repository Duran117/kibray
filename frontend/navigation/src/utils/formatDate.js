import { format } from 'date-fns';
import { enUS, es } from 'date-fns/locale';
import i18n from '../i18n';

export const formatDate = (date, pattern = 'Pp') => {
  try {
    const lng = i18n?.language || 'en';
    const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
    const locale = lng.startsWith('es') ? es : enUS;
    return format(d, pattern, { locale });
  } catch (e) {
    return String(date);
  }
};

export default formatDate;
