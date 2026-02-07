// EChart.tsx
import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { ECharts, EChartsOption } from 'echarts';

interface EChartProps {
  option: EChartsOption;
  style?: React.CSSProperties;
}

export default function EChart({ option, style }: EChartProps) {
  const chartRef = useRef<HTMLDivElement | null>(null);
  const chartInstanceRef = useRef<ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // init only once
    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current);
    }

    chartInstanceRef.current.setOption(option);

    const handleResize = () => {
      chartInstanceRef.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstanceRef.current?.dispose();
      chartInstanceRef.current = null;
    };
  }, [option]);

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height: '400px', ...style }}
    />
  );
}
