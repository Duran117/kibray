import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
  const [assignments, setAssignments] = useState<PMAssignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ project: '', pm: '', role: 'project_manager' });

  const getCsrf = () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  const fetchAssignments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/project-manager-assignments/', {
        headers: { Accept: 'application/json' },
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setAssignments(data.results || data);
    } catch (e: any) {
      setError(e.message || t('pm_assignments.errors.loading', 'Error loading assignments'));
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
          'X-CSRFToken': getCsrf(),
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setShowForm(false);
      setFormData({ project: '', pm: '', role: 'project_manager' });
      fetchAssignments();
    } catch (e: any) {
      setError(e.message || t('pm_assignments.errors.create', 'Error creating assignment'));
    } finally {
      setLoading(false);
    }
  };

  // Instrumentation for Playwright: mark root mounted and log list length
  useEffect(() => {
    const root = document.getElementById('pm-assignments-root');
    if (root) {
      root.setAttribute('data-mounted', '1');
      console.log('[PMAssignments] mounted, count:', assignments.length);
    }
  }, [assignments.length]);

  return (
    <div className="pm-assignments" style={{ padding: 20 }}>
      <h2>{t('pm_assignments.title', 'Project Manager Assignments')}</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button onClick={fetchAssignments} disabled={loading}>
          {t('common.refresh', 'Refresh')}
        </button>
        <button onClick={() => setShowForm(!showForm)} style={{ marginLeft: 'auto' }}>
          {t('pm_assignments.actions.assign_pm', '+ Assign PM')}
        </button>
      </div>

      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} style={{ background: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <h3>{t('pm_assignments.form.new_assignment', 'New PM Assignment')}</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            <input
              placeholder={t('pm_assignments.form.fields.project_id', 'Project ID')}
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              required
            />
            <input
              placeholder={t('pm_assignments.form.fields.pm_user_id', 'PM User ID')}
              value={formData.pm}
              onChange={(e) => setFormData({ ...formData, pm: e.target.value })}
              required
            />
            <input
              placeholder={t('pm_assignments.form.fields.role_placeholder', 'Role (default: project_manager)')}
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={loading}>
                {t('pm_assignments.form.assign', 'Assign')}
              </button>
              <button type="button" onClick={() => setShowForm(false)}>
                {t('common.cancel', 'Cancel')}
              </button>
            </div>
          </div>
        </form>
      )}

      <div style={{ display: 'grid', gap: 12 }}>
        {assignments.map((a) => (
          <div key={a.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, background: '#fff' }}>
            <div>
              <strong>{t('pm_assignments.labels.pm', 'PM')}:</strong> {a.pm_username || `${t('pm_assignments.labels.user', 'User')} ${a.pm}`} → <strong>{t('pm_assignments.labels.project', 'Project')}:</strong> {a.project_name || `#${a.project}`}
            </div>
            <div style={{ fontSize: 12, color: '#666' }}>
              {t('pm_assignments.labels.role', 'Role')}: {a.role} | {t('pm_assignments.labels.created', 'Created')}: {new Date(a.created_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
