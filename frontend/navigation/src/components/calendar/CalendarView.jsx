import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import './CalendarView.css';

const CalendarView = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('month');

  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDay = getFirstDayOfMonth(currentDate);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  return (
    <div className="calendar-view">
      <div className="calendar-header">
        <button onClick={handlePrevMonth}>
          <ChevronLeft size={20} />
        </button>
        <h2>{monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}</h2>
        <button onClick={handleNextMonth}>
          <ChevronRight size={20} />
        </button>
        
        <div className="view-toggle">
          <button 
            onClick={() => setViewMode('month')}
            className={viewMode === 'month' ? 'active' : ''}
          >
            Month
          </button>
          <button 
            onClick={() => setViewMode('week')}
            className={viewMode === 'week' ? 'active' : ''}
          >
            Week
          </button>
          <button 
            onClick={() => setViewMode('day')}
            className={viewMode === 'day' ? 'active' : ''}
          >
            Day
          </button>
        </div>
      </div>

      <div className="calendar-grid">
        {dayNames.map((day, i) => (
          <div key={`day-header-${i}`} className="day-header">
            {day}
          </div>
        ))}
        
        {Array(firstDay).fill(null).map((_, i) => (
          <div key={`empty-${i}`} className="calendar-day empty"></div>
        ))}
        
        {Array(daysInMonth).fill(null).map((_, i) => (
          <div key={`day-${i}`} className="calendar-day">
            <div className="day-number">{i + 1}</div>
            <div className="day-events">
              {/* Events would be rendered here */}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CalendarView;
