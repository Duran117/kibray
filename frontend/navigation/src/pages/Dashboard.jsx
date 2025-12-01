import React from 'react';

export default function Dashboard() {
  return (
    <div data-testid="dashboard" className="dashboard">
      <h1>Dashboard</h1>
      <div className="dashboard-widgets">
        <div className="widget">
          <h2>Projects</h2>
          <p>Active Projects: 5</p>
        </div>
        <div className="widget">
          <h2>Tasks</h2>
          <p>Pending Tasks: 12</p>
        </div>
        <div className="widget">
          <h2>Team</h2>
          <p>Team Members: 8</p>
        </div>
      </div>
    </div>
  );
}
