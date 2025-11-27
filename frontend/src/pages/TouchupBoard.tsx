import { useEffect, useMemo, useState } from 'react';

interface TaskCard {
  id: number;
  title: string;
  priority: 'low'|'medium'|'high'|'urgent';
  assigned_to: number | null;
  due_date: string | null;
  created_at: string;
  completed_at: string | null;
}

type BoardColumns = Record<string, TaskCard[]>;

const PRIORITY_ORDER: Record<TaskCard['priority'], number> = {
  urgent: 3,
  high: 2,
  medium: 1,
  low: 0,
};

export default function TouchupBoard() {
  const [projectId, setProjectId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [columns, setColumns] = useState<BoardColumns>({
    'Pendiente': [],
    'En Progreso': [],
    'Completada': [],
    'Cancelada': [],
  });
  const [total, setTotal] = useState(0);

  const fetchBoard = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL('/api/v1/tasks/touchup_board/', window.location.origin);
      if (projectId) url.searchParams.set('project', projectId);
      const res = await fetch(url.toString(), {
        headers: {
          'Accept': 'application/json',
          'Authorization': localStorage.getItem('access') ? `Bearer ${localStorage.getItem('access')}` : '',
        },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setColumns(data.columns || {});
      setTotal(data.total || 0);
    } catch (e: any) {
      setError(e.message || 'Error loading board');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const sortedColumns = useMemo(() => {
    const sortCards = (cards: TaskCard[]) => [...cards].sort((a, b) => {
      const p = PRIORITY_ORDER[b.priority] - PRIORITY_ORDER[a.priority];
      if (p !== 0) return p;
      const ad = a.due_date ? new Date(a.due_date).getTime() : 0;
      const bd = b.due_date ? new Date(b.due_date).getTime() : 0;
      return ad - bd;
    });
    const out: BoardColumns = {} as any;
    Object.entries(columns).forEach(([k, v]) => (out[k] = sortCards(v as TaskCard[])));
    return out;
  }, [columns]);

  return (
    <div className="touchup-board">
      <div className="toolbar">
        <input
          placeholder="Project ID"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          style={{ padding: '6px 8px', marginRight: 8 }}
        />
        <button onClick={fetchBoard} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
        <span style={{ marginLeft: 12 }}>Total: {total}</span>
        {error && <span style={{ marginLeft: 12, color: 'red' }}>{error}</span>}
      </div>

      <div className="columns" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginTop: 16 }}>
        {(['Pendiente', 'En Progreso', 'Completada', 'Cancelada'] as const).map((col) => (
          <div key={col} className="column" style={{ background: '#f7f7f8', borderRadius: 8, padding: 12 }}>
            <h3 style={{ marginTop: 0 }}>{col}</h3>
            <div className="cards" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {(sortedColumns[col] || []).map((card) => (
                <div key={card.id} className="card" style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong>#{card.id} {card.title}</strong>
                    <span title="Priority" style={{ fontSize: 12 }}>
                      {card.priority.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#555' }}>
                    Due: {card.due_date ? new Date(card.due_date).toLocaleDateString() : '—'}
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button style={{ fontSize: 12 }}>View</button>
                    <button style={{ fontSize: 12 }}>Assign</button>
                    <button style={{ fontSize: 12 }}>Complete</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
