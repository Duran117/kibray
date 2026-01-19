// =============================================================================
// Kibray Gantt - CalendarView Component
// Monthly calendar view (Phase 3)
// =============================================================================

import React, { useState, useMemo } from 'react';
import { GanttItem, GanttCategory } from '../types/gantt';
import { getBarColor } from '../utils/colorUtils';

export interface CalendarViewProps {
  items: GanttItem[];
  categories: GanttCategory[];  // Kept for future category filtering
  onItemClick?: (item: GanttItem) => void;
  onDayClick?: (date: Date) => void;
  canEdit: boolean;
  initialDate?: Date;
}

interface CalendarDay {
  date: Date;
  isCurrentMonth: boolean;
  isToday: boolean;
  isWeekend: boolean;
  items: GanttItem[];
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function startOfWeek(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  return new Date(d.setDate(diff));
}

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function isSameDay(d1: Date, d2: Date): boolean {
  return d1.getFullYear() === d2.getFullYear() &&
         d1.getMonth() === d2.getMonth() &&
         d1.getDate() === d2.getDate();
}

function parseDate(dateStr: string): Date {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day);
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  items,
  categories,
  onItemClick,
  onDayClick,
  canEdit,
  initialDate = new Date(),
}) => {
  const [currentDate, setCurrentDate] = useState(initialDate);
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile
  React.useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart);
    const today = new Date();
    const days: CalendarDay[] = [];
    let day = calendarStart;
    
    for (let i = 0; i < 42; i++) {
      const dayItems = items.filter(item => {
        const start = parseDate(item.start_date);
        const end = parseDate(item.end_date);
        return day >= start && day <= end;
      });
      days.push({
        date: new Date(day),
        isCurrentMonth: day.getMonth() === currentDate.getMonth(),
        isToday: isSameDay(day, today),
        isWeekend: day.getDay() === 0 || day.getDay() === 6,
        items: dayItems,
      });
      day = addDays(day, 1);
    }
    return days;
  }, [currentDate, items]);

  const monthName = currentDate.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });

  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    setSelectedDay(null);
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    setSelectedDay(null);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDay(null);
  };

  const handleDayClick = (day: CalendarDay) => setSelectedDay(day);

  const handleCreateClick = (day: CalendarDay, e: React.MouseEvent) => {
    e.stopPropagation();
    if (canEdit && onDayClick) {
      onDayClick(day.date);
    }
  };

  const handleItemClick = (item: GanttItem, e: React.MouseEvent) => {
    e.stopPropagation();
    onItemClick?.(item);
  };

  const getColor = (item: GanttItem) => {
    return getBarColor(item.status, item.is_milestone, item.is_personal);
  };

  const weekDays = isMobile ? ['D', 'L', 'M', 'X', 'J', 'V', 'S'] : ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'];
  const maxItemsShown = isMobile ? 2 : 3;

  return (
    <div data-testid="calendar-view" className="calendar-view" style={{ display: 'flex', height: '100%', overflow: 'hidden', flexDirection: isMobile && selectedDay ? 'column' : 'row' }}>
      {/* Overlay for mobile sidebar */}
      {isMobile && selectedDay && (
        <div 
          className={`calendar-overlay ${selectedDay ? 'visible' : ''}`}
          onClick={() => setSelectedDay(null)}
        />
      )}
      
      <div className="calendar-main" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: isMobile ? '8px' : '16px' }}>
        {/* Header with navigation */}
        <div className="calendar-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: isMobile ? '8px' : '16px', flexWrap: isMobile ? 'wrap' : 'nowrap', gap: '8px' }}>
          <button 
            onClick={goToPreviousMonth} 
            className="calendar-nav-btn"
            style={{ padding: isMobile ? '10px 14px' : '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', background: '#fff', cursor: 'pointer', minHeight: isMobile ? '44px' : 'auto' }}
          >
            {isMobile ? '←' : 'Anterior'}
          </button>
          <div className="calendar-title-wrapper" style={{ display: 'flex', alignItems: 'center', gap: '12px', order: isMobile ? -1 : 0, width: isMobile ? '100%' : 'auto', justifyContent: isMobile ? 'center' : 'flex-start' }}>
            <h2 className="calendar-title" style={{ fontSize: isMobile ? '1rem' : '1.25rem', fontWeight: '600', textTransform: 'capitalize', margin: 0 }}>{monthName}</h2>
            <button 
              onClick={goToToday} 
              className="calendar-today-btn"
              style={{ padding: '4px 8px', border: '1px solid #d1d5db', borderRadius: '4px', background: '#f9fafb', fontSize: '0.75rem', cursor: 'pointer' }}
            >
              Hoy
            </button>
          </div>
          <button 
            onClick={goToNextMonth} 
            className="calendar-nav-btn"
            style={{ padding: isMobile ? '10px 14px' : '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', background: '#fff', cursor: 'pointer', minHeight: isMobile ? '44px' : 'auto' }}
          >
            {isMobile ? '→' : 'Siguiente'}
          </button>
        </div>

        <div className="calendar-grid" style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div className="calendar-weekdays" style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            {weekDays.map((day, i) => (
              <div key={day} className={`calendar-weekday ${i === 0 || i === 6 ? 'weekend' : ''}`} style={{ padding: isMobile ? '6px 2px' : '8px', textAlign: 'center', fontSize: isMobile ? '0.65rem' : '0.75rem', fontWeight: '600', color: i === 0 || i === 6 ? '#9ca3af' : '#4b5563' }}>{day}</div>
            ))}
          </div>

          <div className="calendar-days" style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gridTemplateRows: 'repeat(6, 1fr)' }}>
            {calendarDays.map((day, index) => {
              const isSelected = selectedDay && isSameDay(day.date, selectedDay.date);
              return (
                <div 
                  key={index} 
                  onClick={() => handleDayClick(day)} 
                  className={`calendar-day ${day.isToday ? 'today' : ''} ${isSelected ? 'selected' : ''} ${!day.isCurrentMonth ? 'other-month' : ''} ${day.isWeekend ? 'weekend' : ''}`}
                  style={{ 
                    padding: isMobile ? '2px' : '4px', 
                    borderRight: (index + 1) % 7 !== 0 ? '1px solid #e5e7eb' : 'none', 
                    borderBottom: index < 35 ? '1px solid #e5e7eb' : 'none', 
                    background: day.isToday ? '#eff6ff' : isSelected ? '#f0f9ff' : day.isWeekend ? '#fafafa' : '#fff', 
                    opacity: day.isCurrentMonth ? 1 : 0.4, 
                    cursor: 'pointer', 
                    minHeight: isMobile ? '45px' : '80px', 
                    display: 'flex', 
                    flexDirection: 'column' 
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '2px' }}>
                    <span 
                      className="calendar-day-number"
                      style={{ 
                        width: isMobile ? '18px' : '24px', 
                        height: isMobile ? '18px' : '24px', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        fontSize: isMobile ? '0.6rem' : '0.75rem', 
                        fontWeight: day.isToday ? '700' : '500', 
                        color: day.isToday ? '#fff' : '#374151', 
                        background: day.isToday ? '#3b82f6' : 'transparent', 
                        borderRadius: '50%' 
                      }}
                    >
                      {day.date.getDate()}
                    </span>
                  </div>
                  <div className={`calendar-day-items ${isMobile ? 'compact' : ''}`} style={{ flex: 1, overflow: 'hidden', display: isMobile ? 'flex' : 'block', flexWrap: 'wrap', gap: isMobile ? '2px' : '0' }}>
                    {isMobile ? (
                      // Mobile: Show dots
                      <>
                        {day.items.slice(0, 4).map((item) => {
                          const color = getColor(item);
                          return (
                            <div 
                              key={item.id} 
                              onClick={(e) => handleItemClick(item, e)} 
                              className="calendar-item"
                              style={{ 
                                width: '6px', 
                                height: '6px', 
                                background: color, 
                                borderRadius: '50%', 
                                cursor: 'pointer' 
                              }} 
                              title={item.title}
                            />
                          );
                        })}
                        {day.items.length > 4 && <div className="calendar-more" style={{ fontSize: '0.5rem', color: '#6b7280' }}>+{day.items.length - 4}</div>}
                      </>
                    ) : (
                      // Desktop: Show text labels
                      <>
                        {day.items.slice(0, maxItemsShown).map((item) => {
                          const color = getColor(item);
                          return (
                            <div 
                              key={item.id} 
                              onClick={(e) => handleItemClick(item, e)} 
                              className="calendar-item"
                              style={{ padding: '2px 4px', marginBottom: '2px', background: color, color: '#fff', fontSize: '0.65rem', borderRadius: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'pointer' }} 
                              title={item.title}
                            >
                              {item.title}
                            </div>
                          );
                        })}
                        {day.items.length > maxItemsShown && <div className="calendar-more" style={{ fontSize: '0.6rem', color: '#6b7280', paddingLeft: '4px' }}>+{day.items.length - maxItemsShown} mas</div>}
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {selectedDay && (
        <div 
          className={`calendar-day-sidebar ${selectedDay ? 'open' : ''}`}
          style={{ 
            width: isMobile ? '100%' : '320px', 
            borderLeft: isMobile ? 'none' : '1px solid #e5e7eb', 
            background: '#f9fafb', 
            display: 'flex', 
            flexDirection: 'column', 
            overflow: 'hidden',
            ...(isMobile ? {
              position: 'fixed',
              bottom: 0,
              left: 0,
              right: 0,
              maxHeight: '70vh',
              borderRadius: '16px 16px 0 0',
              boxShadow: '0 -4px 20px rgba(0,0,0,0.15)',
              zIndex: 100
            } : {})
          }}
        >
          {/* Mobile drag handle */}
          {isMobile && (
            <div className="calendar-sidebar-handle" style={{ width: '40px', height: '4px', background: '#d1d5db', borderRadius: '2px', margin: '8px auto' }} />
          )}
          
          <div className="calendar-sidebar-header" style={{ padding: isMobile ? '12px 16px' : '16px', borderBottom: '1px solid #e5e7eb', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div className="calendar-sidebar-weekday" style={{ fontSize: '0.75rem', color: '#6b7280' }}>{selectedDay.date.toLocaleDateString('es-ES', { weekday: 'long' })}</div>
              <div className="calendar-sidebar-date" style={{ fontSize: '1.25rem', fontWeight: '600' }}>{selectedDay.date.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' })}</div>
            </div>
            <div className="calendar-sidebar-actions" style={{ display: 'flex', gap: '8px' }}>
              {canEdit && onDayClick && (
                <button 
                  onClick={(e) => handleCreateClick(selectedDay, e)} 
                  className="calendar-sidebar-btn primary"
                  style={{ width: isMobile ? '40px' : '28px', height: isMobile ? '40px' : '28px', border: 'none', background: '#3b82f6', color: '#fff', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', fontWeight: '500' }}
                  title="Crear item en este día"
                >
                  +
                </button>
              )}
              <button 
                onClick={() => setSelectedDay(null)} 
                className="calendar-sidebar-btn close"
                style={{ width: isMobile ? '40px' : '28px', height: isMobile ? '40px' : '28px', border: 'none', background: '#f3f4f6', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                ✕
              </button>
            </div>
          </div>
          <div className="calendar-sidebar-content" style={{ flex: 1, overflow: 'auto', padding: isMobile ? '12px' : '16px', WebkitOverflowScrolling: 'touch' }}>
            {selectedDay.items.length === 0 ? (
              <div className="calendar-empty" style={{ textAlign: 'center', color: '#9ca3af', padding: isMobile ? '24px 16px' : '32px 16px' }}>
                <div className="calendar-empty-icon" style={{ fontSize: '2rem', marginBottom: '8px' }}>📅</div>
                <div>No hay items para este dia</div>
                {canEdit && onDayClick && (
                  <button
                    onClick={(e) => handleCreateClick(selectedDay, e)}
                    className="calendar-create-btn"
                    style={{ marginTop: '12px', padding: isMobile ? '12px 20px' : '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '0.875rem', fontWeight: '500', minHeight: isMobile ? '44px' : 'auto' }}
                  >
                    + Crear Item
                  </button>
                )}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedDay.items.map((item) => {
                  const color = getColor(item);
                  return (
                    <div 
                      key={item.id} 
                      onClick={(e) => handleItemClick(item, e)} 
                      className="calendar-item-card"
                      style={{ background: '#fff', borderRadius: '8px', padding: isMobile ? '10px' : '12px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', borderLeft: '4px solid ' + color }}
                    >
                      <div className="calendar-item-title" style={{ fontWeight: '500', marginBottom: '4px', fontSize: isMobile ? '0.9rem' : '1rem' }}>{item.title}</div>
                      {item.description && <div className="calendar-item-desc" style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '4px' }}>{item.description}</div>}
                      <div className="calendar-item-tags" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <span className="calendar-item-tag" style={{ fontSize: '0.65rem', padding: '2px 6px', background: '#f3f4f6', borderRadius: '4px', color: '#4b5563' }}>{item.start_date} - {item.end_date}</span>
                        {item.assigned_to_name && <span className="calendar-item-tag" style={{ fontSize: '0.65rem', padding: '2px 6px', background: '#e0f2fe', borderRadius: '4px', color: '#0369a1' }}>{item.assigned_to_name}</span>}
                        <span className="calendar-item-tag" style={{ fontSize: '0.65rem', padding: '2px 6px', background: color + '20', borderRadius: '4px', color }}>{item.percent_complete}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;
