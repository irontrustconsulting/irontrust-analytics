// App.tsx
import EChart from '../Echart';
import type { AvgEntropyResult } from '../../types/types';


// src/components/charts/AvgEntropyChart.tsx
import type { EChartsOption } from 'echarts';

interface AvgEntropyChartProps {
  data: AvgEntropyResult[];
}

export function AvgEntropyChart({ data }: AvgEntropyChartProps) {
  const labels = data.map(row => row.qname);
  const entropies = data.map(row => row.avg_entropy);

  const option: EChartsOption = {
    title: {
      text: 'Average Entropy per Domain',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      bottom: 140, // similar to Plotly margin.b
      left: 80,
      right: 40,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45, // Plotly tickangle: -45 equivalent
        interval: 0,
      },
      name: 'Domain',
      nameLocation: 'middle',
      nameGap: 90,
    },
    yAxis: {
      type: 'value',
      name: 'Average Entropy',
    },
    series: [
      {
        type: 'bar',
        data: entropies,
        itemStyle: {
          color: 'rgba(55, 128, 191, 0.7)',
        },
      },
    ],
  };

  return <EChart option={option} style={{ height: '600px' }} />;
}

