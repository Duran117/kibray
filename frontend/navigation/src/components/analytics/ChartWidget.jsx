import React from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import './ChartWidget.css';

const ChartWidget = ({ title, type, data, height = 300 }) => {
  const renderChart = () => {
    // Transform data for recharts format
    const chartData = type === 'doughnut' || type === 'pie'
      ? data.datasets[0].data.map((value, index) => ({
          name: data.labels[index],
          value
        }))
      : data.labels.map((label, index) => ({
          name: label,
          ...data.datasets.reduce((acc, dataset, datasetIndex) => ({
            ...acc,
            [`data${datasetIndex}`]: dataset.data[index]
          }), {})
        }));

    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e5e7eb)" />
              <XAxis dataKey="name" stroke="var(--text-secondary, #6b7280)" />
              <YAxis stroke="var(--text-secondary, #6b7280)" />
              <Tooltip 
                contentStyle={{
                  background: 'var(--bg-primary, #ffffff)',
                  border: '1px solid var(--border, #e5e7eb)',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              {data.datasets.map((dataset, idx) => (
                <Line
                  key={idx}
                  type="monotone"
                  dataKey={`data${idx}`}
                  stroke={dataset.borderColor}
                  name={dataset.label}
                  strokeWidth={2}
                  dot={{ fill: dataset.borderColor, r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e5e7eb)" />
              <XAxis dataKey="name" stroke="var(--text-secondary, #6b7280)" />
              <YAxis stroke="var(--text-secondary, #6b7280)" />
              <Tooltip 
                contentStyle={{
                  background: 'var(--bg-primary, #ffffff)',
                  border: '1px solid var(--border, #e5e7eb)',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              {data.datasets.map((dataset, idx) => (
                <Bar
                  key={idx}
                  dataKey={`data${idx}`}
                  fill={dataset.backgroundColor[0] || dataset.borderColor}
                  name={dataset.label}
                  radius={[8, 8, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'doughnut':
      case 'pie':
        const COLORS = data.datasets[0].backgroundColor;
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={type === 'doughnut' ? 80 : 100}
                innerRadius={type === 'doughnut' ? 50 : 0}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  background: 'var(--bg-primary, #ffffff)',
                  border: '1px solid var(--border, #e5e7eb)',
                  borderRadius: '8px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="chart-widget">
      <div className="chart-header">
        <h3 className="chart-title">{title}</h3>
      </div>
      <div className="chart-content">
        {renderChart()}
      </div>
    </div>
  );
};

export default ChartWidget;
