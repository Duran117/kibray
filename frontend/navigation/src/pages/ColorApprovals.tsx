import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

interface ColorApproval {
  id: number;
  project: number;
  project_name?: string;
  color_name: string;
  color_code: string;
  brand: string;
  location: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  requested_by: number;
  approved_by: number | null;
  notes: string;
  created_at: string;
  approved_at: string | null;
}

export default function ColorApprovals() {
  const { t } = useTranslation();
  const [approvals, setApprovals] = useState<ColorApproval[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({ project: '', status: '', brand: '' });
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [formData, setFormData] = useState({
    project: '',
    color_name: '',
    color_code: '',
    brand: '',
    location: '',
    notes: '',
  });

  // Helper to get CSRF token from meta tag (Django renders this in base template)
  const getCsrf = () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

  const fetchApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filter.project) params.set('project', filter.project);
      if (filter.status) params.set('status', filter.status);
      if (filter.brand) params.set('brand', filter.brand);

      const res = await fetch(`/api/v1/color-approvals/?${params}`, {
        headers: { Accept: 'application/json' },
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setApprovals(data.results || data);
    } catch (e: any) {
      setError(e.message || t('color_approvals.errors.loading', 'Error loading approvals'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/color-approvals/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setShowRequestForm(false);
      setFormData({ project: '', color_name: '', color_code: '', brand: '', location: '', notes: '' });
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || t('color_approvals.errors.create', 'Error creating approval request'));
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: number, signatureFile?: File) => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      if (signatureFile) formData.append('client_signature', signatureFile);
      const res = await fetch(`/api/v1/color-approvals/${id}/approve/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf() },
        credentials: 'include',
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || t('color_approvals.errors.approve', 'Error approving'));
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (id: number, reason: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/color-approvals/${id}/reject/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        credentials: 'include',
        body: JSON.stringify({ reason }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || t('color_approvals.errors.reject', 'Error rejecting'));
    } finally {
      setLoading(false);
    }
  };

  // Instrumentation: mark root mounted for Playwright and log early state
  useEffect(() => {
    const root = document.getElementById('color-approvals-root');
    if (root) {
      root.setAttribute('data-mounted', '1');
      console.log('[ColorApprovals] mounted, approvals length:', approvals.length);
    }
  }, [approvals.length]);

  return (
    <div className="color-approvals" style={{ padding: 20 }}>
      <h2>{t('color_approvals.title', 'Color Approvals')}</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          placeholder={t('color_approvals.filters.project_id', 'Project ID')}
          value={filter.project}
          onChange={(e) => setFilter({ ...filter, project: e.target.value })}
          style={{ padding: '6px 8px' }}
        />
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          style={{ padding: '6px 8px' }}
        >
          <option value="">{t('color_approvals.filters.all_statuses', 'All statuses')}</option>
          <option value="PENDING">{t('common.pending', 'Pending')}</option>
          <option value="APPROVED">{t('common.approved_note', 'Approved')}</option>
          <option value="REJECTED">{t('common.rejected_note', 'Rejected')}</option>
        </select>
        <input
          placeholder={t('color_approvals.filters.brand', 'Brand')}
          value={filter.brand}
          onChange={(e) => setFilter({ ...filter, brand: e.target.value })}
          style={{ padding: '6px 8px' }}
        />
        <button onClick={fetchApprovals} disabled={loading}>
          {t('common.refresh', 'Refresh')}
        </button>
        <button onClick={() => setShowRequestForm(!showRequestForm)} style={{ marginLeft: 'auto' }}>
          {t('color_approvals.actions.request_approval', '+ Request Approval')}
        </button>
      </div>

      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      {showRequestForm && (
        <form onSubmit={handleRequestSubmit} style={{ background: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <h3>{t('color_approvals.form.new_request_title', 'New Approval Request')}</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            <input
              placeholder={t('color_approvals.form.fields.project_id', 'Project ID')}
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              required
            />
            <input
              placeholder={t('color_approvals.form.fields.color_name', 'Color Name')}
              value={formData.color_name}
              onChange={(e) => setFormData({ ...formData, color_name: e.target.value })}
              required
            />
            <input
              placeholder={t('color_approvals.form.fields.color_code', 'Color Code')}
              value={formData.color_code}
              onChange={(e) => setFormData({ ...formData, color_code: e.target.value })}
            />
            <input
              placeholder={t('color_approvals.form.fields.brand', 'Brand')}
              value={formData.brand}
              onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
            />
            <input
              placeholder={t('color_approvals.form.fields.location', 'Location')}
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
            <textarea
              placeholder={t('color_approvals.form.fields.notes', 'Notes')}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={loading}>
                {t('color_approvals.form.submit', 'Submit')}
              </button>
              <button type="button" onClick={() => setShowRequestForm(false)}>
                {t('common.cancel', 'Cancel')}
              </button>
            </div>
          </div>
        </form>
      )}

      <div style={{ display: 'grid', gap: 12 }}>
        {approvals.map((approval) => (
          <div key={approval.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, background: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <strong>
                  {approval.color_name} ({approval.color_code})
                </strong>{' '}
                - {approval.brand}
                <div style={{ fontSize: 12, color: '#666' }}>
                  {t('color_approvals.labels.location', 'Location')}: {approval.location} | {t('color_approvals.labels.status', 'Status')}: <strong>{approval.status}</strong>
                </div>
                <div style={{ fontSize: 12, color: '#666' }}>{t('color_approvals.labels.created', 'Created')}: {new Date(approval.created_at).toLocaleString()}</div>
                {approval.notes && <div style={{ fontSize: 12, marginTop: 4 }}>{approval.notes}</div>}
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                {approval.status === 'PENDING' && (
                  <>
                    <button
                      onClick={() => {
                        // TODO: Add file input for signature upload
                        handleApprove(approval.id);
                      }}
                      style={{ fontSize: 12 }}
                    >
                      {t('common.approve', 'Approve')}
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt(t('color_approvals.prompts.rejection_reason', 'Rejection reason:'));
                        if (reason) handleReject(approval.id, reason);
                      }}
                      style={{ fontSize: 12 }}
                    >
                      {t('common.reject', 'Reject')}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
