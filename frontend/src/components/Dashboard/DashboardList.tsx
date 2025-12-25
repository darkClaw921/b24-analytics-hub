import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardsService } from '../../services/dashboards'
import { DashboardListItem } from '../../types'
import { useAuth } from '../../hooks/useAuth'

export default function DashboardList() {
  const [dashboards, setDashboards] = useState<DashboardListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewDashboard, setShowNewDashboard] = useState(false)
  const [newDashboardTitle, setNewDashboardTitle] = useState('')
  const [newDashboardDescription, setNewDashboardDescription] = useState('')
  
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  useEffect(() => {
    loadDashboards()
  }, [])

  const loadDashboards = async () => {
    try {
      const dashboardsData = await dashboardsService.getDashboards()
      setDashboards(dashboardsData)
    } catch (error) {
      console.error('Error loading dashboards:', error)
    } finally {
      setLoading(false)
    }
  }

  const createDashboard = async () => {
    if (!newDashboardTitle.trim()) return

    try {
      const dashboard = await dashboardsService.createDashboard(
        newDashboardTitle,
        newDashboardDescription || undefined
      )
      navigate(`/dashboards/${dashboard.id}`)
    } catch (error) {
      console.error('Error creating dashboard:', error)
      alert('Ошибка при создании дашборда')
    }
  }

  const deleteDashboard = async (dashboardId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!window.confirm('Вы уверены, что хотите удалить этот дашборд?')) {
      return
    }

    try {
      await dashboardsService.deleteDashboard(dashboardId)
      await loadDashboards()
    } catch (error) {
      console.error('Error deleting dashboard:', error)
      alert('Ошибка при удалении дашборда')
    }
  }

  return (
    <div className="dashboard-list-page">
      <header className="app-header">
        <h1>B24 Analytics Hub</h1>
        <div className="header-actions">
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

      <div className="dashboard-list-container">
        <div className="dashboard-list-header">
          <h2>Мои дашборды</h2>
          {dashboards.length > 0 && (
            <button className="btn btn-primary" onClick={() => setShowNewDashboard(true)}>
              Новый дашборд
            </button>
          )}
        </div>

        {showNewDashboard && (
          <div className="new-dashboard-form">
            <input
              type="text"
              placeholder="Название дашборда"
              value={newDashboardTitle}
              onChange={(e) => setNewDashboardTitle(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createDashboard()}
            />
            <textarea
              placeholder="Описание (необязательно)"
              value={newDashboardDescription}
              onChange={(e) => setNewDashboardDescription(e.target.value)}
              rows={3}
            />
            <div className="form-actions">
              <button className="btn btn-primary" onClick={createDashboard}>
                Создать
              </button>
              <button className="btn btn-secondary" onClick={() => {
                setShowNewDashboard(false)
                setNewDashboardTitle('')
                setNewDashboardDescription('')
              }}>
                Отмена
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="loading">Загрузка...</div>
        ) : dashboards.length === 0 ? (
          <div className="empty-state">
            <p>У вас пока нет дашбордов</p>
            <button className="btn btn-primary" onClick={() => setShowNewDashboard(true)}>
              Создать первый дашборд
            </button>
          </div>
        ) : (
          <div className="dashboard-grid">
            {dashboards.map((dashboard) => (
              <div
                key={dashboard.id}
                className="dashboard-card"
                onClick={() => navigate(`/dashboards/${dashboard.id}`)}
              >
                <div className="dashboard-card-header">
                  <h3>{dashboard.title}</h3>
                  <button
                    className="btn-icon"
                    onClick={(e) => deleteDashboard(dashboard.id, e)}
                    title="Удалить"
                  >
                    ×
                  </button>
                </div>
                {dashboard.description && (
                  <p className="dashboard-description">{dashboard.description}</p>
                )}
                <div className="dashboard-card-footer">
                  <span className="dashboard-date">
                    Обновлен: {new Date(dashboard.updated_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

