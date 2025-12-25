import React from 'react'
import { PieChart as RechartsPieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ChartData } from '../../types'

interface PieChartProps {
  data: ChartData
}

export const PieChart: React.FC<PieChartProps> = ({ data }) => {
  console.log('PieChart render:', { data, labels: data.labels, datasets: data.datasets })
  
  // Для pie chart используем первый dataset
  const dataset = data.datasets[0] || { label: 'Data', data: [] }
  
  // Преобразуем данные в формат для recharts
  const chartData = data.labels.map((label, index) => ({
    name: label,
    value: dataset.data[index] || 0,
  }))

  console.log('PieChart chartData:', chartData)

  const colors = data.datasets[0]?.backgroundColor 
    ? [data.datasets[0].backgroundColor]
    : chartData.map((_, index) => `hsl(${(index * 360) / chartData.length}, 70%, 50%)`)

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '250px', position: 'relative', display: 'flex', flexDirection: 'column' }}>
      <ResponsiveContainer width="100%" height="100%" minHeight={250}>
        <RechartsPieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius="80%"
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  )
}

