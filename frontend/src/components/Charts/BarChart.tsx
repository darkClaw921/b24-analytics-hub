import React, { useRef, useEffect, useState } from 'react'
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { ChartData } from '../../types'

interface BarChartProps {
  data: ChartData
}

export const BarChart: React.FC<BarChartProps> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 250 })

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({
          width: rect.width || 800,
          height: Math.max(rect.height || 250, 250)
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  console.log('BarChart render:', { data, labels: data.labels, datasets: data.datasets, dimensions })
  
  // Преобразуем данные в формат для recharts
  const chartData = data.labels.map((label, index) => {
    const point: Record<string, any> = { name: label }
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index]
    })
    return point
  })

  console.log('BarChart chartData:', chartData)

  const colors = data.datasets.map((dataset, index) => 
    dataset.backgroundColor || `hsl(${(index * 360) / data.datasets.length}, 70%, 50%)`
  )

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '250px', position: 'relative' }}>
      {dimensions.width > 0 && dimensions.height > 0 && (
        <ResponsiveContainer width={dimensions.width} height={dimensions.height}>
          <RechartsBarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            {data.datasets.map((dataset, index) => (
              <Bar
                key={dataset.label}
                dataKey={dataset.label}
                fill={colors[index]}
              />
            ))}
          </RechartsBarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

