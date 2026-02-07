import React from 'react';
import { Bar, Line } from 'react-chartjs-2'; // Import Chart types for Line and Bar charts
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';

// Register necessary components for Chart.js
ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

interface ChartProps {
  queryId: string;
  data: any; // The query result data passed from the parent component
}

const Chart: React.FC<ChartProps> = ({ queryId, data }) => {
  // Check if data is valid
  if (!data || data.labels.length === 0 || data.values.length === 0) {
    return <div>No data available for this query.</div>;
  }

  // Basic chart setup
  const chartData = {
    labels: data.labels || [],  // X-axis labels (qname, client_ip, etc.)
    datasets: [
      {
        label: queryId,
        data: data.values || [],  // Y-axis values (query count, entropy, etc.)
        fill: false,
        borderColor: 'rgba(75, 192, 192, 1)', // Line color
        backgroundColor: 'rgba(75, 192, 192, 0.2)', // Bar color with transparency
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    scales: {
      x: {
        beginAtZero: true,
        grid: {
          color: '#ccc',  // Light grid lines
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: '#ccc',  // Light grid lines
        },
      },
    },
  };

  // Handle histogram binning for avg_entropy
  const createHistogramData = (values: number[]) => {
    const bins = 10; // Number of bins
    const min = Math.min(...values);
    const max = Math.max(...values);
    const binWidth = (max - min) / bins;
    const binCounts = Array(bins).fill(0);
    
    // Bin the values
    values.forEach(value => {
      const binIndex = Math.floor((value - min) / binWidth);
      if (binIndex >= bins) {
        binCounts[bins - 1] += 1; // Push any out-of-range values into the last bin
      } else {
        binCounts[binIndex] += 1;
      }
    });

    // Create the histogram chart data
    const histogramLabels = Array.from({ length: bins }, (_, i) => {
      const binStart = min + i * binWidth;
      const binEnd = binStart + binWidth;
      return `${binStart.toFixed(2)} - ${binEnd.toFixed(2)}`;
    });

    return {
      labels: histogramLabels,
      values: binCounts,
    };
  };

  // Conditional rendering based on queryId
  switch (queryId) {
    case 'avg_entropy': {
      const histogramData = createHistogramData(data.values);
      return (
        <div>
          <h3>Average Entropy (Histogram)</h3>
          <Bar
            data={{
              labels: histogramData.labels,
              datasets: [{
                label: 'Frequency',
                data: histogramData.values,
                backgroundColor: 'rgba(75, 192, 192, 0.6)', // Bar color for histogram
              }],
            }}
            options={{
              ...chartOptions,
              indexAxis: 'x', // Standard bar chart
            }}
          />
        </div>
      );
    }

    case 'qname_length':
      return (
        <div>
          <h3>Qname Length</h3>
          <Bar
            data={{
              labels: data.labels,
              datasets: [{
                ...chartData.datasets[0],
                indexAxis: 'y', // This makes it horizontal
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Customize the bar color
              }],
            }}
            options={chartOptions}
          />
        </div>
      );

    case 'top_domains':
      return (
        <div>
          <h3>Top Domains</h3>
          <Bar
            data={{
              labels: data.labels,
              datasets: [{
                ...chartData.datasets[0],
                indexAxis: 'y', // Horizontal bar chart for top domains
                backgroundColor: 'rgba(54, 162, 235, 0.6)', // Customize the bar color
              }],
            }}
            options={chartOptions}
          />
        </div>
      );

    case 'top_query_types':
      return (
        <div>
          <h3>Top Query Types</h3>
          <Bar data={chartData} options={chartOptions} />
        </div>
      );

    case 'topn_clients':
      return (
        <div>
          <h3>Top Clients</h3>
          <Bar data={chartData} options={chartOptions} />
        </div>
      );

    default:
      return <div>Unsupported Query Type</div>;
  }
};

export default Chart;
