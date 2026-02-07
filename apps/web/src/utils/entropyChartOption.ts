// entropyChartOption.ts
import type { EChartsOption } from 'echarts';
import { buildEntropyChartData } from '../preprocessors/transform';
import type { AvgEntropyResult } from '../types/types';

export function getEntropyChartOption(
  results: AvgEntropyResult[]
): EChartsOption {
  const { categories, entropyValues, queryCounts } =
    buildEntropyChartData(results);

  return {
    title: {
      text: 'DNS Average Entropy by Domain',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const idx = params[0].dataIndex;
        return `
          <strong>${categories[idx]}</strong><br/>
          Avg Entropy: ${entropyValues[idx].toFixed(3)}<br/>
          Query Count: ${queryCounts[idx]}
        `;
      },
    },
    grid: {
      left: 200, // space for long domain names
      right: 40,
    },
    xAxis: {
      type: 'value',
      name: 'Average Entropy',
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        width: 180,
        overflow: 'truncate',
      },
    },
    series: [
      {
        name: 'Avg Entropy',
        type: 'bar',
        data: entropyValues,
        itemStyle: {
          color: '#5470C6',
        },
      },
    ],
  };
}
