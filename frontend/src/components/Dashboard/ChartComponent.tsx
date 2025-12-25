import React from 'react'
import { ChartWrapper } from '../Charts/ChartWrapper'
import type { Chart, ChartData } from '../../types'

interface ChartComponentProps {
  chart: Chart
  data: ChartData
  onRefresh?: () => void
}

const ChartComponent: React.FC<ChartComponentProps> = ({ chart, data, onRefresh }) => {
  console.log('ChartComponent render:', { 
    chartId: chart.id, 
    chartType: chart.chart_type, 
    data,
    hasLabels: !!data?.labels,
    labelsLength: data?.labels?.length,
    hasDatasets: !!data?.datasets,
    datasetsLength: data?.datasets?.length
  })
  
  if (!data) {
    return <div className="chart-error">Ошибка: данные чарта отсутствуют</div>
  }
  
  if (!data.labels || !Array.isArray(data.labels)) {
    return <div className="chart-error">Ошибка: labels отсутствуют или не являются массивом</div>
  }
  
  if (!data.datasets || !Array.isArray(data.datasets) || data.datasets.length === 0) {
    return <div className="chart-error">Ошибка: datasets отсутствуют или пусты</div>
  }
  
  return (
    <div className="chart-wrapper" style={{ width: '100%', height: '100%', flex: '1 1 auto' }}>
      {onRefresh && (
        <button className="btn-refresh" onClick={onRefresh} title="Обновить данные">
          ↻
        </button>
      )}
      <ChartWrapper type={chart.chart_type} data={data} />
    </div>
  )
}

export default ChartComponent

