import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { dashboardsService } from '../../services/dashboards'
import { Dashboard, ChartData } from '../../types'
import ChartComponent from './ChartComponent'
import ChartEditor from './ChartEditor'
import ResizableChartContainer from './ResizableChartContainer'
import { useAuth } from '../../hooks/useAuth'

export default function DashboardView() {
  const { dashboardId } = useParams<{ dashboardId: string }>()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [editingChart, setEditingChart] = useState<number | null>(null)
  const [showNewChart, setShowNewChart] = useState(false)
  const [chartDataCache, setChartDataCache] = useState<Record<number, ChartData>>({})

  useEffect(() => {
    if (dashboardId) {
      loadDashboard()
    }
  }, [dashboardId])

  const loadDashboard = async () => {
    if (!dashboardId) return
    
    try {
      const dashboardData = await dashboardsService.getDashboard(parseInt(dashboardId))
      setDashboard(dashboardData)
      
      // Загружаем данные для всех чартов
      for (const chart of dashboardData.charts) {
        await loadChartData(chart.id)
      }
    } catch (error) {
      console.error('Error loading dashboard:', error)
      alert('Ошибка при загрузке дашборда')
    } finally {
      setLoading(false)
    }
  }

  const loadChartData = async (chartId: number) => {
    try {
      const result = await dashboardsService.executeChart(chartId)
      console.log(`Chart ${chartId} execution result:`, JSON.stringify(result, null, 2))
      if (result.success && result.data) {
        console.log(`Chart ${chartId} data:`, JSON.stringify(result.data, null, 2))
        console.log(`Chart ${chartId} data structure:`, {
          labels: result.data.labels,
          labelsLength: result.data.labels?.length,
          datasets: result.data.datasets,
          datasetsLength: result.data.datasets?.length
        })
        setChartDataCache(prev => ({ ...prev, [chartId]: result.data! }))
      } else {
        console.error(`Chart ${chartId} execution failed:`, result.error)
      }
    } catch (error) {
      console.error(`Error loading chart ${chartId} data:`, error)
    }
  }

  const handleChartCreated = () => {
    setShowNewChart(false)
    loadDashboard()
  }

  const handleChartUpdated = () => {
    setEditingChart(null)
    loadDashboard()
  }

  const handleChartDeleted = async (chartId: number) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот чарт?')) {
      return
    }

    try {
      await dashboardsService.deleteChart(chartId)
      await loadDashboard()
    } catch (error) {
      console.error('Error deleting chart:', error)
      alert('Ошибка при удалении чарта')
    }
  }

  if (loading) {
    return (
      <div className="dashboard-view-page">
        <div className="loading">Загрузка...</div>
      </div>
    )
  }

  if (!dashboard) {
    return (
      <div className="dashboard-view-page">
        <div className="error">Дашборд не найден</div>
      </div>
    )
  }

  return (
    <div className="dashboard-view-page">
      <header className="app-header">
        <h1>{dashboard.title}</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/dashboards')}>
            ← Назад к дашбордам
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/')}>
            Чаты
          </button>
          {user?.is_admin && (
            <button className="btn btn-secondary" onClick={() => navigate('/admin')}>
              Админ-панель
            </button>
          )}
          <button className="btn btn-secondary" onClick={logout}>
            Выйти
          </button>
        </div>
      </header>

      {dashboard.description && (
        <div className="dashboard-description-section">
          <p>{dashboard.description}</p>
        </div>
      )}

      {dashboard.charts.length > 0 && (
        <div className="dashboard-actions">
          <button className="btn btn-primary" onClick={() => setShowNewChart(true)}>
            Добавить чарт
          </button>
        </div>
      )}

      {showNewChart && (
        <ChartEditor
          dashboardId={dashboard.id}
          onClose={() => setShowNewChart(false)}
          onSave={handleChartCreated}
        />
      )}

      {editingChart && (
        <ChartEditor
          dashboardId={dashboard.id}
          chartId={editingChart}
          onClose={() => setEditingChart(null)}
          onSave={handleChartUpdated}
        />
      )}

      <div className="dashboard-charts-grid">
        {dashboard.charts.length === 0 ? (
          <div className="empty-state">
            <p>В этом дашборде пока нет чартов</p>
            <button className="btn btn-primary" onClick={() => setShowNewChart(true)}>
              Добавить первый чарт
            </button>
          </div>
        ) : (
          dashboard.charts.map((chart) => (
            <ResizableChartContainer
              key={chart.id}
              chart={chart}
              gridCellSize={100}
              onResize={(width, height) => {
                // Размер уже сохранен в БД через ResizableChartContainer
                // Обновляем локальное состояние для немедленного отображения
                if (dashboard) {
                  const updatedCharts = dashboard.charts.map(c => 
                    c.id === chart.id ? { ...c, width, height } : c
                  )
                  setDashboard({ ...dashboard, charts: updatedCharts })
                }
              }}
              onMove={(positionX, positionY) => {
                // Позиция уже сохранена в БД через ResizableChartContainer
                // Обновляем локальное состояние для немедленного отображения
                if (dashboard) {
                  const updatedCharts = dashboard.charts.map(c => 
                    c.id === chart.id ? { ...c, position_x: positionX, position_y: positionY } : c
                  )
                  setDashboard({ ...dashboard, charts: updatedCharts })
                }
              }}
            >
              <div className="chart-header">
                <h3>{chart.title}</h3>
                <div className="chart-actions">
                  <button
                    className="btn-icon"
                    onClick={() => setEditingChart(chart.id)}
                    title="Редактировать"
                  >
                    ✎
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => handleChartDeleted(chart.id)}
                    title="Удалить"
                  >
                    ×
                  </button>
                </div>
              </div>
              <div className="chart-content">
                {chartDataCache[chart.id] ? (
                  <ChartComponent
                    chart={chart}
                    data={chartDataCache[chart.id]}
                    onRefresh={() => loadChartData(chart.id)}
                  />
                ) : (
                  <div className="chart-loading">Загрузка данных...</div>
                )}
              </div>
            </ResizableChartContainer>
          ))
        )}
      </div>
    </div>
  )
}

