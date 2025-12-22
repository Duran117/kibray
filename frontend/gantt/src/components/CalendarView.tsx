// =============================================================================
// Kibray Gantt - CalendarView Component
// Monthly calendar view (Phase 3)
// =============================================================================

import React, { useState, useMemo } from 'react';
import { GanttItem, GanttCategory } from '../types/gantt';
import { getBarColor } from '../utils/colorUtils';

export interface CalendarViewProps {
  items: GanttItem[];
  categories: GanttCategory[];
  onItemClick?: (item: GanttItem) => void;
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
  canEdit,
  initialDate = new Date(),
}) => {
  const [currentDate, setCurrentDate] = useState(initialDate);
  const [selectedDay, setSelectedDay] = useState<CalendarDay | null>(null);

  const categoryMap = useMemo(() => {
    const map = new Map<number, GanttCategory>();
    categories.forEach(cat => map.set(cat.id, cat));
    return map;
  }, [categories]);

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

  const handleItemClick = (item: GanttItem, e: React.MouseEvent) => {
    e.stopPropagation();
    onItemClick?.(item);
  };

  const getColor = (item: GanttItem) => {
    return getBarColor(item.status, item.is_milestone, item.is_personal);
  };

  const weekDays = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'];

  return (
    <div data-testid="calendar-view" style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <button onClick={goToPreviousMonth} style={{ padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', background: '#fff', cursor: 'pointer' }}>Anterior</button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', textTransform: 'capitalize', margin: 0 }}>{monthName}</h2>
            <button onClick={goToToday} style={{ padding: '4px 8px', border: '1px solid #d1d5db', borderRadius: '4px', background: '#f9fafb', fontSize: '0.75rem', cursor: 'pointer' }}>Hoy</button>
          </div>
          <button onClick={goToNextMonth} style={{ padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: '6px', background: '#fff', cursor: 'pointer' }}>Siguiente</button>
        </div>

        <div className="calendar-grid" style={{ flex: 1, display: 'flex', flexDirection: 'column', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            {weekDays.map((day, i) => (
              <div key={day} style={{ padding: '8px', textAlign: 'center', fontSize: '0.75rem', fontWeight: '600', color: i === 0 || i === 6 ? '#9ca3af' : '#4b5563' }}>{day}</div>
            ))}
          </div>

          <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gridTemplateRows: 'repeat(6, 1fr)' }}>
            {calendarDays.map((day, index) => {
              const isSelected = selectedDay && isSameDay(day.date, selectedDay.date);
              return (
                <div key={index} onClick={() => handleDayClick(day)} style={{ padding: '4px', borderRight: (index + 1) % 7 !== 0 ? '1px solid #e5e7eb' : 'none', borderBottom: index < 35 ? '1px solid #e5e7eb' : 'none', background: day.isToday ? '#eff6ff' : isSelected ? '#f0f9ff' : day.isWeekend ? '#fafafa' : '#fff', opacity: day.isCurrentMonth ? 1 : 0.4, cursor: 'pointer', minHeight: '80px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '2px' }}>
                    <span style={{ width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: day.isToday ? '700' : '500', color: day.isToday ? '#fff' : '#374151', background: day.isToday ? '#3b82f6' : 'transparent', borderRadius: '50%' }}>{day.date.getDate()}</span>
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    {day.items.slice(0, 3).map((item) => {
                      const color = getColor(item);
                      return (
                        <div key={item.id} onClick={(e) => handleItemClick(item, e)} style={{ padding: '2px 4px', marginBottom: '2px', background: color, color: '#fff', fontSize: '0.65rem', borderRadius: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'pointer' }} title={item.title}>{item.title}</div>
                      );
                    })}
                    {day.items.length > 3 && <div style={{ fontSize: '0.6rem', color: '#6b7280', paddingLeft: '4px' }}>+{day.items.length - 3} mas</div>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {selectedDay && (
        <div style={{ width: '320px', borderLeft: '1px solid #e5e7eb', background: '#f9fafb', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{selectedDay.date.toLocaleDateString('es-ES', { weekday: 'long' })}</div>
              <div style={{ fontSize: '1.25rem', fontWeight: '600' }}>{selectedDay.date.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' })}</div>
            </div>
            <button onClick={() => setSelectedDay(null)} style={{ width: '28px', height: '28px', border: 'none', background: '#f3f4f6', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>X</button>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
            {selectedDay.items.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#9ca3af', padding: '32px 16px' }}>
                <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📅</div>
                <div>No hay items para este dia</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedDay.items.map((item) => {
                  const color = getColor(item);
                  return (
                    <div key={item.id} onClick={(e) => handleItemClick(item, e)} style={{ background: '#fff', borderRadius: '8px', padding: '12px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)', cursor: 'pointer', borderLeft: '4px solid ' + color }}>
                      <div style={{ fontWeight: '500', marginBottom: '4px' }}>{item.title}</div>
                      {item.description && <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '4px' }}>{item.description}</div>}
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: '#f3f4f6', borderRadius: '4px', color: '#4b5563' }}>{item.start_date} - {item.end_date}</span>
                        {item.assigned_to_name && <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: '#e0f2fe', borderRadius: '4px', color: '#0369a1' }}>{item.assigned_to_name}</span>}
                        <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: color + '20', borderRadius: '4px', color: color }}>{item.percent_complete}%</span>
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
