// src/components/SensitivityHeatmap.tsx
import React, { useMemo } from "react";
import {
  Chart as ChartJS,
  Tooltip,
  Legend,
  LinearScale,
  type ChartOptions,
} from "chart.js";
import { MatrixController, MatrixElement } from "chartjs-chart-matrix";
import { Chart } from "react-chartjs-2";

ChartJS.register(Tooltip, Legend, LinearScale, MatrixController, MatrixElement);

type Props = {
  grid: number[][];      // grid[row = Terminal Growth][col = WACC]
  rowLabels?: string[];  // Terminal Growth (low → high)
  colLabels?: string[];  // WACC (low → high)
  title?: string;
};

// Simple continuous color scale
function colorFor(val: number, min: number, max: number) {
  if (max === min) return "rgba(0,0,0,0.2)";
  const t = (val - min) / (max - min); // 0..1
  const r = Math.floor(255 * t);
  const g = Math.floor(255 * Math.min(1, 2 * (1 - Math.abs(t - 0.5))));
  const b = Math.floor(255 * (1 - t));
  return `rgba(${r},${g},${b},0.9)`;
}

export default function SensitivityHeatmap({ grid, rowLabels, colLabels, title }: Props) {
  const rows = grid.length;                // Terminal Growth count
  const cols = grid[0]?.length ?? 0;       // WACC count

  const { minV, maxV } = useMemo(() => {
    let minV = Infinity, maxV = -Infinity;
    grid.forEach(r => r.forEach(v => { if (v < minV) minV = v; if (v > maxV) maxV = v; }));
    return { minV, maxV };
  }, [grid]);

  // x = row index (Terminal Growth), y = col index (WACC)
  const data = useMemo(() => {
    const cells: Array<{ x: number; y: number; v: number }> = [];
    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        cells.push({ x: i, y: j, v: grid[i][j] });
      }
    }
    return {
      datasets: [
        {
          label: "Intrinsic value ($/sh)",
          data: cells,
          parsing: { xAxisKey: "x", yAxisKey: "y" },
          backgroundColor: (ctx: any) => colorFor(ctx.raw?.v, minV, maxV),
          hoverBackgroundColor: (ctx: any) => colorFor(ctx.raw?.v, minV, maxV),
          borderColor: "rgba(255,255,255,0.9)",
          borderWidth: 1,
          // 👇 make each cell fill its bin
          width: (ctx: any) => {
            const x = ctx.chart.scales.x;
            return Math.abs(x.getPixelForValue(1) - x.getPixelForValue(0)) - 1; // -1 to leave a hairline grid
          },
          height: (ctx: any) => {
            const y = ctx.chart.scales.y;
            return Math.abs(y.getPixelForValue(1) - y.getPixelForValue(0)) - 1;
          },
        },
      ],
    };
  }, [grid, rows, cols, minV, maxV]);

  const options = useMemo<ChartOptions<"matrix">>(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items: any[]) => {
            const raw = items[0].raw;
            const tgIdx = raw.x as number;   // Terminal Growth index
            const waccIdx = raw.y as number; // WACC index
            const tgLabel = rowLabels?.[tgIdx] ?? `g ${tgIdx + 1}`;
            const waccLabel = colLabels?.[waccIdx] ?? `WACC ${waccIdx + 1}`;
            return `${waccLabel} • ${tgLabel}`;
          },
          label: (item: any) => ` $${(item.raw?.v as number).toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: rows - 0.5,
        ticks: {
          stepSize: 1,
          callback: (value: any) => {
            const idx = Number(value);
            return rowLabels?.[idx] ?? `${idx}`;
          },
        },
        grid: { display: false },
        title: { display: true, text: "Terminal Growth (g)" },
      },
      y: {
        type: "linear",
        min: 0,
        max: cols - 0.5,
        ticks: {
          stepSize: 1,
          callback: (value: any) => {
            const idx = Number(value);
            return colLabels?.[idx] ?? `${idx}`;
          },
        },
        grid: { display: false },
        title: { display: true, text: "WACC" },
      },
    },
    animation: { duration: 0 }, // or: animation: false as const
  }), [rows, cols, rowLabels, colLabels]);

  return (
    <div>
      {title && <div className="mb-2 font-medium">{title}</div>}
      <div className="w-full h-[360px]">
        <Chart type="matrix" data={data} options={options} />
      </div>
      <div className="mt-3 text-xs text-muted-foreground">
        Scale: ${minV.toFixed(2)} → ${maxV.toFixed(2)}
      </div>
    </div>
  );
}
