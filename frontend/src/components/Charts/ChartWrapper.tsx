import React from 'react'
import { LineChart } from './LineChart'
import { BarChart } from './BarChart'
import { PieChart } from './PieChart'
import type { ChartType, ChartData } from '../../types'

interface ChartWrapperProps {
  type: ChartType
  data: ChartData
}

export const ChartWrapper: React.FC<ChartWrapperProps> = ({ type, data }) => {
  console.log('ChartWrapper render:', { type, data })
  
  switch (type) {
    case 'line':
      return <LineChart data={data} />
    case 'bar':
      return <BarChart data={data} />
    case 'pie':
      return <PieChart data={data} />
    default:
      return <div>Unknown chart type: {type}</div>
  }
}

