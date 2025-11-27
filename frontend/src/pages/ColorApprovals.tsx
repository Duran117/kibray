import React, { useState, useEffect } from 'react';

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

  const fetchApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filter.project) params.set('project', filter.project);
      if (filter.status) params.set('status', filter.status);
      if (filter.brand) params.set('brand', filter.brand);

      const res = await fetch(`/api/v1/color-approvals/?${params}`, {
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setApprovals(data.results || data);
    } catch (e: any) {
      setError(e.message || 'Error loading approvals');
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
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setShowRequestForm(false);
      setFormData({ project: '', color_name: '', color_code: '', brand: '', location: '', notes: '' });
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || 'Error creating approval request');
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
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || 'Error approving');
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
          Authorization: `Bearer ${localStorage.getItem('access')}`,
        },
        body: JSON.stringify({ reason }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      fetchApprovals();
    } catch (e: any) {
      setError(e.message || 'Error rejecting');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="color-approvals" style={{ padding: 20 }}>
      <h2>Color Approvals</h2>
      <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          placeholder="Project ID"
          value={filter.project}
          onChange={(e) => setFilter({ ...filter, project: e.target.value })}
          style={{ padding: '6px 8px' }}
        />
        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          style={{ padding: '6px 8px' }}
        >
          <option value="">All statuses</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
        <input
          placeholder="Brand"
          value={filter.brand}
          onChange={(e) => setFilter({ ...filter, brand: e.target.value })}
          style={{ padding: '6px 8px' }}
        />
        <button onClick={fetchApprovals} disabled={loading}>
          Refresh
        </button>
        <button onClick={() => setShowRequestForm(!showRequestForm)} style={{ marginLeft: 'auto' }}>
          + Request Approval
        </button>
      </div>

      {error && <div style={{ color: 'red', marginBottom: 12 }}>{error}</div>}

      {showRequestForm && (
        <form onSubmit={handleRequestSubmit} style={{ background: '#f9f9f9', padding: 12, borderRadius: 8, marginBottom: 16 }}>
          <h3>New Approval Request</h3>
          <div style={{ display: 'grid', gap: 8 }}>
            <input
              placeholder="Project ID"
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              required
            />
            <input
              placeholder="Color Name"
              value={formData.color_name}
              onChange={(e) => setFormData({ ...formData, color_name: e.target.value })}
              required
            />
            <input
              placeholder="Color Code"
              value={formData.color_code}
              onChange={(e) => setFormData({ ...formData, color_code: e.target.value })}
            />
            <input
              placeholder="Brand"
              value={formData.brand}
              onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
            />
            <input
              placeholder="Location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
            <textarea
              placeholder="Notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" disabled={loading}>
                Submit
              </button>
              <button type="button" onClick={() => setShowRequestForm(false)}>
                Cancel
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
                  Location: {approval.location} | Status: <strong>{approval.status}</strong>
                </div>
                <div style={{ fontSize: 12, color: '#666' }}>Created: {new Date(approval.created_at).toLocaleString()}</div>
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
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt('Rejection reason:');
                        if (reason) handleReject(approval.id, reason);
                      }}
                      style={{ fontSize: 12 }}
                    >
                      Reject
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
