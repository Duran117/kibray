import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const API_BASE = '/api/v1';

// Types
interface ProjectHealth {
  project_id: number;
  project_name: string;
  completion_percentage: number;
  budget: {
    total: number;
    spent: number;
    remaining: number;
    variance_pct: number;
  };
  timeline: {
    start_date: string | null;
    end_date: string | null;
    days_total: number | null;
    days_elapsed: number | null;
    days_remaining: number | null;
    on_track: boolean | null;
  };
  task_summary: {
    total: number;
    completed: number;
    in_progress: number;
    pending: number;
    cancelled: number;
  };
  risk_indicators: {
    overdue_tasks: number;
    budget_overrun: boolean;
    behind_schedule: boolean;
  };
  recent_activity: {
    completions_last_7_days: number;
  };
}

interface TouchupAnalytics {
  total_touchups: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  completion_rate: number;
  avg_resolution_time_hours: number;
  trends: Array<{ date: string; count: number }>;
}

interface ColorApprovalAnalytics {
  total_approvals: number;
  by_status: Record<string, number>;
  by_brand: Array<{ brand: string; count: number }>;
  avg_approval_time_hours: number;
  pending_aging_days: number;
}

interface PMPerformance {
  pm_list: Array<{
    pm_id: number;
    pm_username: string;
    projects_count: number;
    tasks_assigned: number;
    tasks_completed: number;
    completion_rate: number;
    overdue_count: number;
  }>;
  overall: {
    total_pms: number;
    avg_projects_per_pm: number;
    avg_completion_rate: number;
  };
}

const COLORS = {
  primary: '#3b82f6',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  purple: '#a855f7',
  pink: '#ec4899',
  gray: '#6b7280',
};

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'project' | 'touchups' | 'approvals' | 'pms'>('project');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [projectHealth, setProjectHealth] = useState<ProjectHealth | null>(null);
  const [touchupData, setTouchupData] = useState<TouchupAnalytics | null>(null);
  const [approvalData, setApprovalData] = useState<ColorApprovalAnalytics | null>(null);
  const [pmData, setPmData] = useState<PMPerformance | null>(null);

  const getAuthToken = () => localStorage.getItem('token');

  const fetchProjectHealth = async (pid: number) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/analytics/projects/${pid}/health/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setProjectHealth(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch project health');
    } finally {
      setLoading(false);
    }
  };

  const fetchTouchupAnalytics = async (pid?: number) => {
    try {
      setLoading(true);
      setError(null);
      const url = pid
        ? `${API_BASE}/analytics/touchups/?project=${pid}`
        : `${API_BASE}/analytics/touchups/`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setTouchupData(response.data);
    } catch (err: any) {
      setError('Failed to fetch touchup analytics');
    } finally {
      setLoading(false);
    }
  };

  const fetchColorApprovalAnalytics = async (pid?: number) => {
    try {
      setLoading(true);
      setError(null);
      const url = pid
        ? `${API_BASE}/analytics/color-approvals/?project=${pid}`
        : `${API_BASE}/analytics/color-approvals/`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setApprovalData(response.data);
    } catch (err: any) {
      setError('Failed to fetch color approval analytics');
    } finally {
      setLoading(false);
    }
  };

  const fetchPMPerformance = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE}/analytics/pm-performance/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setPmData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch PM performance');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'project' && projectId) {
      fetchProjectHealth(projectId);
    } else if (activeTab === 'touchups') {
      fetchTouchupAnalytics(projectId || undefined);
    } else if (activeTab === 'approvals') {
      fetchColorApprovalAnalytics(projectId || undefined);
    } else if (activeTab === 'pms') {
      fetchPMPerformance();
    }
  }, [activeTab, projectId]);

  // Project Health Tab
  const renderProjectHealth = () => {
    if (!projectHealth) {
      return (
        <div className="text-center py-8">
          <p className="text-gray-600">Enter a Project ID to view health metrics</p>
        </div>
      );
    }

    const taskStatusData = [
      { name: 'Completed', value: projectHealth.task_summary.completed, color: COLORS.success },
      { name: 'In Progress', value: projectHealth.task_summary.in_progress, color: COLORS.info },
      { name: 'Pending', value: projectHealth.task_summary.pending, color: COLORS.warning },
      { name: 'Cancelled', value: projectHealth.task_summary.cancelled, color: COLORS.gray },
    ];

    const budgetData = [
      { name: 'Spent', value: projectHealth.budget.spent },
      { name: 'Remaining', value: projectHealth.budget.remaining },
    ];

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-900">{projectHealth.project_name}</h2>
          <p className="text-sm text-gray-500 mt-1">Project ID: {projectHealth.project_id}</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Completion</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">
              {projectHealth.completion_percentage.toFixed(1)}%
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Budget Remaining</div>
            <div className="mt-2 text-3xl font-bold text-green-600">
              ${projectHealth.budget.remaining.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              of ${projectHealth.budget.total.toLocaleString()}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Timeline Status</div>
            <div className="mt-2">
              {projectHealth.timeline.on_track === true && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  On Track
                </span>
              )}
              {projectHealth.timeline.on_track === false && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                  Behind Schedule
                </span>
              )}
              {projectHealth.timeline.on_track === null && (
                <span className="text-gray-500">N/A</span>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Overdue Tasks</div>
            <div className="mt-2 text-3xl font-bold text-orange-600">
              {projectHealth.risk_indicators.overdue_tasks}
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Task Status Pie Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Task Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={taskStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {taskStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Budget Bar Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Overview</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={budgetData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill={COLORS.primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Indicators */}
        {(projectHealth.risk_indicators.budget_overrun ||
          projectHealth.risk_indicators.behind_schedule ||
          projectHealth.risk_indicators.overdue_tasks > 0) && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Risk Alerts</h3>
                <div className="mt-2 text-sm text-red-700">
                  <ul className="list-disc list-inside space-y-1">
                    {projectHealth.risk_indicators.budget_overrun && (
                      <li>Budget overrun detected</li>
                    )}
                    {projectHealth.risk_indicators.behind_schedule && (
                      <li>Project is behind schedule</li>
                    )}
                    {projectHealth.risk_indicators.overdue_tasks > 0 && (
                      <li>{projectHealth.risk_indicators.overdue_tasks} overdue tasks</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Touchup Analytics Tab
  const renderTouchupAnalytics = () => {
    if (!touchupData) return null;

    const statusData = Object.entries(touchupData.by_status).map(([name, value]) => ({
      name,
      value,
    }));

    const priorityData = Object.entries(touchupData.by_priority).map(([name, value]) => ({
      name,
      value,
    }));

    return (
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Total Touch-ups</div>
            <div className="mt-2 text-3xl font-bold text-purple-600">
              {touchupData.total_touchups}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Completion Rate</div>
            <div className="mt-2 text-3xl font-bold text-green-600">
              {touchupData.completion_rate.toFixed(1)}%
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Avg Resolution Time</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">
              {touchupData.avg_resolution_time_hours.toFixed(1)}h
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Completed</div>
            <div className="mt-2 text-3xl font-bold text-green-600">
              {touchupData.by_status['Completada'] || 0}
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Status Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill={COLORS.purple} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Priority Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Priority Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={priorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {priorityData.map((_entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={[COLORS.danger, COLORS.warning, COLORS.info, COLORS.gray][index]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Trends Line Chart */}
        {touchupData.trends.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Completion Trends (Last 30 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={touchupData.trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" stroke={COLORS.primary} name="Completions" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  };

  // Color Approval Analytics Tab
  const renderColorApprovalAnalytics = () => {
    if (!approvalData) return null;

    const statusData = Object.entries(approvalData.by_status).map(([name, value]) => ({
      name,
      value,
    }));

    return (
      <div className="space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Total Approvals</div>
            <div className="mt-2 text-3xl font-bold text-indigo-600">
              {approvalData.total_approvals}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Pending</div>
            <div className="mt-2 text-3xl font-bold text-yellow-600">
              {approvalData.by_status['PENDING'] || 0}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Avg Approval Time</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">
              {approvalData.avg_approval_time_hours.toFixed(1)}h
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Oldest Pending</div>
            <div className="mt-2 text-3xl font-bold text-orange-600">
              {approvalData.pending_aging_days}d
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Status Pie Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Approval Status</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((_entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={[COLORS.warning, COLORS.success, COLORS.danger][index]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Brand Analysis Bar Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Brands</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={approvalData.by_brand.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="brand" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill={COLORS.info} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  // PM Performance Tab
  const renderPMPerformance = () => {
    if (!pmData) return null;

    return (
      <div className="space-y-6">
        {/* Overall Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Total PMs</div>
            <div className="mt-2 text-3xl font-bold text-purple-600">
              {pmData.overall.total_pms}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Avg Projects per PM</div>
            <div className="mt-2 text-3xl font-bold text-blue-600">
              {pmData.overall.avg_projects_per_pm.toFixed(1)}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-600">Avg Completion Rate</div>
            <div className="mt-2 text-3xl font-bold text-green-600">
              {pmData.overall.avg_completion_rate.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* PM Performance Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">PM Completion Rates</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={pmData.pm_list}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="pm_username" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="completion_rate" fill={COLORS.success} name="Completion Rate %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* PM Details Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  PM
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Projects
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tasks Assigned
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tasks Completed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completion Rate
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Overdue
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {pmData.pm_list.map((pm) => (
                <tr key={pm.pm_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {pm.pm_username}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pm.projects_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pm.tasks_assigned}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pm.tasks_completed}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        pm.completion_rate >= 80
                          ? 'bg-green-100 text-green-800'
                          : pm.completion_rate >= 60
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {pm.completion_rate.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pm.overdue_count > 0 ? (
                      <span className="text-red-600 font-medium">{pm.overdue_count}</span>
                    ) : (
                      <span className="text-gray-400">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">Comprehensive project metrics and performance insights</p>
        </div>

        {/* Project ID Filter */}
        {(activeTab === 'project' || activeTab === 'touchups' || activeTab === 'approvals') && (
          <div className="bg-white rounded-lg shadow p-4 mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {activeTab === 'project' ? 'Project ID (Required)' : 'Project ID (Optional - Leave empty for all)'}
            </label>
            <input
              type="number"
              value={projectId || ''}
              onChange={(e) => setProjectId(e.target.value ? parseInt(e.target.value) : null)}
              placeholder="Enter project ID"
              className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('project')}
                className={`${
                  activeTab === 'project'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Project Health
              </button>
              <button
                onClick={() => setActiveTab('touchups')}
                className={`${
                  activeTab === 'touchups'
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Touch-ups
              </button>
              <button
                onClick={() => setActiveTab('approvals')}
                className={`${
                  activeTab === 'approvals'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Color Approvals
              </button>
              <button
                onClick={() => setActiveTab('pms')}
                className={`${
                  activeTab === 'pms'
                    ? 'border-green-500 text-green-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                PM Performance
              </button>
            </nav>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="text-gray-600 mt-4">Loading analytics...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <>
            {activeTab === 'project' && renderProjectHealth()}
            {activeTab === 'touchups' && renderTouchupAnalytics()}
            {activeTab === 'approvals' && renderColorApprovalAnalytics()}
            {activeTab === 'pms' && renderPMPerformance()}
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
