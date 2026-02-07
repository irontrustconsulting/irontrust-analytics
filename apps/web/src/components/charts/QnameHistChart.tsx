//import React from 'react';
import { bin } from 'd3-array';
import EChart from '../Echart';
import type { EChartsOption } from 'echarts';
import type { QnameLengthResult } from '../../types/types';

interface QnameLengthChartProps {
  data: QnameLengthResult[];  // Assuming data is an array of objects with qname_length
}

export function QnameHistChart({ data }: QnameLengthChartProps) {
  // Extract the qname_length values
  const qnameLengths = data.map(d => d.qname_length);

  // Dynamically compute the min and max values from the qname_lengths
  const minValue = Math.min(...qnameLengths);
  const maxValue = Math.max(...qnameLengths);

  // Set the bin size or number of bins
  //const binSize = 5; // Adjust bin size as needed
  const binCount = 20 //Math.floor((maxValue - minValue) / binSize);

  // Use d3.bin() to create binning function
  const binning = bin()
    .domain([minValue, maxValue])   // Set the domain based on min and max values
    .thresholds(binCount);           // Number of bins or threshold size
  
  // Apply binning to the qnameLengths data
  const bins = binning(qnameLengths);

  // Prepare the binned data with bin range and counts
  const binnedData = bins.map((bin) => {
    const rangeStart = bin.x0 || 0;         // Starting point of the bin
    const rangeEnd = bin.x1 || 0;           // Ending point of the bin
    const midpoint = (rangeStart+ rangeEnd) / 2; // Midpoint for bar chart placement

    return {
      range: `${rangeStart}-${rangeEnd}`,
      midpoint: midpoint,
      count: bin.length,  // Number of qname_length values in this bin
    };
  });

  // Extract data for chart rendering
  const labels = binnedData.map(bin => bin.range);
  const midpoints = binnedData.map(bin => bin.midpoint);  // Midpoints for X-axis
  const frequencies = binnedData.map(bin => bin.count);    // Frequency counts for Y-axis

  // Define ECharts options
  const option: EChartsOption = {
    title: {
      text: 'DNS Query Length Distribution',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const idx = params[0].dataIndex;
        return `${labels[idx]}<br/>Frequency: ${frequencies[idx]}`;
      },
    },
    xAxis: {
      type: 'category',
      data: midpoints,  // Use midpoints for X-axis
      name: 'Qname Length',
    },
    yAxis: {
      type: 'value',
      name: 'Frequency',
    },
    series: [
      {
        type: 'bar',
        data: frequencies,
        itemStyle: {
          color: 'rgba(55, 128, 191, 0.7)',
        },
      },
    ],
    markLine: {
      data: [
        {
          type: 'average',
          name: 'Typical Upper Bound',
          lineStyle: {
            type: 'dashed',
            color: 'red',
            width: 2,
          },
          yAxis: 50,  // Set the upper bound here
        },
      ],
    },
  };

  return <EChart option={option} style={{ height: '600px' }} />;
}
