import React, { useState, useEffect } from 'react';
import ChartWidget from './ChartWidget';
import KPICard from './KPICard';
import * as api from '../../utils/api';
import { TrendingUp, DollarSign, Users, Clock, BarChart3, Download, AlertCircle } from 'lucide-react';
import './AnalyticsDashboard.css';
import { useTranslation } from 'react-i18next';

const AnalyticsDashboard = () => {
  const { t } = useTranslation();
  const [analyticsData, setAnalyticsData] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get(`/nav-analytics/?range=${timeRange}`);
      setAnalyticsData(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(t('analytics.error_loading', 'Failed to load dashboard data. Please try again.'));
      setAnalyticsData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    console.log('Exporting analytics...');
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner"></div>
        <p>{t('analytics.loading', 'Loading analytics...')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <AlertCircle size={48} />
        <h3>{t('analytics.error_title', 'Error Loading Dashboard')}</h3>
        <p>{error}</p>
        <button onClick={fetchAnalytics} className="retry-btn">
          {t('common.retry', 'Retry')}
        </button>
      </div>
    );
  }

  if (!analyticsData || !analyticsData.kpis) {
    return (
      <div className="analytics-error">
        <BarChart3 size={48} />
        <h3>{t('analytics.no_data_title', 'No Data Available')}</h3>
        <p>{t('analytics.no_data_message', 'Analytics data is not available at this time.')}</p>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <div className="analytics-title-section">
          <BarChart3 size={28} />
          <h1 className="analytics-title">{t('analytics.title', 'Analytics Dashboard')}</h1>
        </div>
        <div className="analytics-controls">
          <select 
            className="time-range-select" 
            value={timeRange} 
            onChange={e => setTimeRange(e.target.value)}
          >
            <option value="7d">{t('analytics.time_ranges.7d', 'Last 7 Days')}</option>
            <option value="30d">{t('analytics.time_ranges.30d', 'Last 30 Days')}</option>
            <option value="90d">{t('analytics.time_ranges.90d', 'Last 90 Days')}</option>
            <option value="1y">{t('analytics.time_ranges.1y', 'Last Year')}</option>
          </select>
          <button className="export-btn" onClick={handleExport}>
            <Download size={18} />
            {t('analytics.export_report', 'Export Report')}
          </button>
        </div>
      </div>

      <div className="kpi-grid">
        <KPICard
          title={t('analytics.kpis.total_revenue', 'Total Revenue')}
          value={`$${((analyticsData.kpis.total_revenue || analyticsData.kpis.totalRevenue || 0) / 1000000).toFixed(2)}M`}
          icon={<DollarSign size={24} />}
          trend={{ value: 12, direction: 'up' }}
          color="green"
        />
        <KPICard
          title={t('analytics.kpis.active_projects', 'Active Projects')}
          value={analyticsData.kpis.active_projects || analyticsData.kpis.activeProjects || 0}
          icon={<BarChart3 size={24} />}
          trend={{ value: 8, direction: 'up' }}
          color="blue"
        />
        <KPICard
          title={t('analytics.kpis.team_members', 'Team Members')}
          value={analyticsData.kpis.team_members || analyticsData.kpis.teamMembers || 0}
          icon={<Users size={24} />}
          trend={{ value: 5, direction: 'up' }}
          color="purple"
        />
        <KPICard
          title={t('analytics.kpis.avg_completion', 'Avg Completion')}
          value={`${analyticsData.kpis.avg_completion || analyticsData.kpis.avgCompletion || 0}%`}
          icon={<Clock size={24} />}
          trend={{ value: 3, direction: 'down' }}
          color="orange"
        />
      </div>

      {(analyticsData.budgetChart || analyticsData.projectProgress) && (
        <div className="charts-grid">
          {analyticsData.budgetChart && (
            <ChartWidget
              title={t('analytics.charts.budget_vs_actual', 'Budget vs Actual')}
              type="line"
              data={analyticsData.budgetChart}
              height={300}
            />
          )}
          {analyticsData.projectProgress && (
            <ChartWidget
              title={t('analytics.charts.project_status', 'Project Status')}
              type="doughnut"
              data={analyticsData.projectProgress}
              height={300}
            />
          )}
          {analyticsData.taskDistribution && (
            <ChartWidget
              title={t('analytics.charts.task_distribution', 'Task Distribution')}
              type="bar"
              data={analyticsData.taskDistribution}
              height={300}
            />
          )}
          {analyticsData.monthlyTrends && (
            <ChartWidget
              title={t('analytics.charts.monthly_trends', 'Monthly Trends')}
              type="line"
              data={analyticsData.monthlyTrends}
              height={300}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
