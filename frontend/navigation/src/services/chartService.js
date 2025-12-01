// Chart Service - Data transformation and chart utilities
export const chartService = {
  /**
   * Transform API data to chart format
   * @param {Object} apiData - Raw API data
   * @param {string} chartType - Chart type
   * @returns {Object} Chart-ready data
   */
  transformForChart(apiData, chartType) {
    switch (chartType) {
      case 'line':
      case 'bar':
        return this.transformSeriesData(apiData);
      case 'pie':
      case 'doughnut':
        return this.transformCategoryData(apiData);
      default:
        return apiData;
    }
  },

  /**
   * Transform series data (line/bar charts)
   */
  transformSeriesData(data) {
    if (!data || !data.series) return { labels: [], datasets: [] };

    return {
      labels: data.labels || [],
      datasets: data.series.map(series => ({
        label: series.name,
        data: series.data,
        borderColor: series.color || this.getRandomColor(),
        backgroundColor: series.bgColor || this.getRandomColor(0.1),
        tension: 0.4
      }))
    };
  },

  /**
   * Transform category data (pie/doughnut charts)
   */
  transformCategoryData(data) {
    if (!data || !data.categories) return { labels: [], datasets: [] };

    return {
      labels: data.categories.map(cat => cat.name),
      datasets: [{
        data: data.categories.map(cat => cat.value),
        backgroundColor: data.categories.map((cat, idx) => 
          cat.color || this.getColorPalette()[idx % this.getColorPalette().length]
        )
      }]
    };
  },

  /**
   * Get color palette
   */
  getColorPalette() {
    return [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // orange
      '#ef4444', // red
      '#8b5cf6', // purple
      '#ec4899', // pink
      '#14b8a6', // teal
      '#f97316'  // orange-red
    ];
  },

  /**
   * Generate random color
   */
  getRandomColor(alpha = 1) {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  },

  /**
   * Calculate trend
   */
  calculateTrend(current, previous) {
    if (!previous || previous === 0) return { value: 0, direction: 'neutral' };
    
    const change = ((current - previous) / previous) * 100;
    return {
      value: Math.abs(Math.round(change)),
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral'
    };
  },

  /**
   * Format number for display
   */
  formatNumber(num, options = {}) {
    const {
      decimals = 0,
      prefix = '',
      suffix = '',
      shorthand = false
    } = options;

    if (shorthand) {
      if (num >= 1000000) {
        return `${prefix}${(num / 1000000).toFixed(decimals)}M${suffix}`;
      }
      if (num >= 1000) {
        return `${prefix}${(num / 1000).toFixed(decimals)}K${suffix}`;
      }
    }

    return `${prefix}${num.toFixed(decimals)}${suffix}`;
  },

  /**
   * Aggregate data by time period
   */
  aggregateByPeriod(data, period = 'day') {
    // Implementation for grouping data by hour/day/week/month
    // This would depend on your data structure
    return data;
  },

  /**
   * Calculate moving average
   */
  calculateMovingAverage(data, windowSize = 7) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (i < windowSize - 1) {
        result.push(null);
      } else {
        const window = data.slice(i - windowSize + 1, i + 1);
        const average = window.reduce((sum, val) => sum + val, 0) / windowSize;
        result.push(Math.round(average));
      }
    }
    return result;
  }
};

export default chartService;
