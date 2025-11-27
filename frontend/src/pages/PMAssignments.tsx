import React, { useState, useEffect } from 'react';

interface PMAssignment {
  id: number;
  project: number;
  project_name?: string;
  pm: number;
  pm_username?: string;
  role: string;
  created_at: string;
}

export default function PMAssignments() {
  const [assignments, setAssignments] = useState<PMAssignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ project: '', pm: '', role: 'project_manager' });

  const fetchAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/project-manager-assignments/', {
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAssignments(data.results || data);
    } catch (e: any) {
      setError(e.message || 'Error loading assignments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/project-manager-assignments/assign/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setShowForm(false);
      setFormData({ project: '', pm: '', role: 'project_manager' });
      fetchAssignments();
    } catch (e: any) {
      setError(e.message || 'Error creating assignment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pm-assignments" style={{ padding: 20 }}>
      <h2>Project Manager Assignments</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={fetchAssignments} disabled={loading}>
          Refresh
        </button>
        <button onClick={() => setShowForm(!showForm)} style={{ marginLeft: 'auto' }}>
          + Assign PM
        </button>
      </div>

      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} style={{ background: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <h3>New PM Assignment</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            <input
              placeholder="Project ID"
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              required
            />
            <input
              placeholder="PM User ID"
              value={formData.pm}
              onChange={(e) => setFormData({ ...formData, pm: e.target.value })}
              required
            />
            <input
              placeholder="Role (default: project_manager)"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={loading}>
                Assign
              </button>
              <button type="button" onClick={() => setShowForm(false)}>
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      <div style={{ display: 'grid', gap: 12 }}>
        {assignments.map((a) => (
          <div key={a.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, background: '#fff' }}>
            <div>
              <strong>PM:</strong> {a.pm_username || `User ${a.pm}`} → <strong>Project:</strong> {a.project_name || `#${a.project}`}
            </div>
            <div style={{ fontSize: 12, color: '#666' }}>
              Role: {a.role} | Created: {new Date(a.created_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
