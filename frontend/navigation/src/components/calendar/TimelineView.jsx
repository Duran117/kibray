import React from 'react';
import './TimelineView.css';

const TimelineView = () => {
  const mockEvents = [
    { id: 1, title: 'Project Kickoff', date: '2024-01-15', type: 'milestone' },
    { id: 2, title: 'Design Phase Complete', date: '2024-02-20', type: 'milestone' },
    { id: 3, title: 'Foundation Work', date: '2024-03-10 - 2024-04-05', type: 'task' },
    { id: 4, title: 'Framing Started', date: '2024-04-10', type: 'task' },
    { id: 5, title: 'Inspection Scheduled', date: '2024-05-15', type: 'milestone' },
    { id: 6, title: 'Interior Work', date: '2024-06-01 - 2024-07-30', type: 'task' },
    { id: 7, title: 'Final Walkthrough', date: '2024-08-15', type: 'milestone' }
  ];

  return (
    <div className="timeline-view">
      <h2>Project Timeline</h2>
      <div className="timeline-container">
        {mockEvents.map(event => (
          <div key={event.id} className="timeline-item">
            <div className={`timeline-marker ${event.type}`}></div>
            <div className="timeline-content">
              <h4>{event.title}</h4>
              <p className="timeline-date">{event.date}</p>
              <span className={`timeline-badge ${event.type}`}>
                {event.type}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimelineView;
