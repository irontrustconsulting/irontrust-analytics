// src/components/charts/QnameLengthChart.tsx
import EChart from '../Echart';
import type { QnameLengthResult } from '../../types/types';
import type { EChartsOption } from 'echarts';

interface QnameLengthChartProps {
  data: QnameLengthResult[];
}

export function QnameLengthChart({ data }: QnameLengthChartProps) {
  // Sort the data by qname_length in descending order
  const sortedData = [...data].sort((a, b) => a.qname_length - b.qname_length); // Descending order

  // Extract the sorted labels and values
  const labels = sortedData.map(row => row.qname);
  const qname_lengths = sortedData.map(row => row.qname_length);

  // ECharts option configuration
  const option: EChartsOption = {
    title: {
      text: 'Sorted Qname Lengths (Descending)',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const idx = params[0].dataIndex;
        return `${labels[idx]}<br/>Qname Length: ${qname_lengths[idx]}`;
      },
    },
    grid: {
      left: 150,
      right: 50,
      bottom: 80,
    },
    xAxis: {
      type: 'value',
      name: 'Qname Length',
      nameLocation: 'middle',
      nameGap: 60,
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: {
        rotate: 45, // Rotate label for readability
        width: 180, // Truncate long names if necessary
        overflow: 'truncate',
      },
    },
    series: [
      {
        type: 'bar',
        data: qname_lengths,
        itemStyle: {
          color: 'rgba(55, 128, 191, 0.7)', // Same color as before
        },
      },
    ],
  };

  return <EChart option={option} style={{ height: '600px' }} />;
}
